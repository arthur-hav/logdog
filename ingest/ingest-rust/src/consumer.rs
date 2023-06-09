use std::str::FromStr;

use amqprs::{
    channel::{
        BasicAckArguments, BasicConsumeArguments, Channel, QueueBindArguments,
        QueueDeclareArguments,
    },
    connection::Connection as amqpConnection,
    connection::OpenConnectionArguments,
    consumer::AsyncConsumer,
    BasicProperties, Deliver,
};
use async_trait::async_trait;
use chrono;
use futures::pin_mut;
use lazy_static::lazy_static;
use regex::Regex;
use tokio::sync::{mpsc, Notify};
use tokio_postgres::{
    binary_copy::BinaryCopyInWriter,
    connect,
    types::{ToSql, Type},
    NoTls,
};
use tracing::{info, metadata};
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

#[derive(Debug)]

pub struct LogRow {
    time: chrono::DateTime<chrono::Utc>,
    shard: i32,
    data: serde_json::Value,
    level: String,
    words: Vec<String>,
}

impl LogRow {
    pub fn new(data: &str, shard: &i32) -> Self {
        let mut deser_res = serde_json::from_str(data);
        if deser_res.is_err() {
            let mut default_map = serde_json::Map::new();
            let message = serde_json::Value::from_str(data.clone());
            if message.is_ok() {
                default_map["message"] = message.unwrap();
            }
            deser_res = Ok(serde_json::Value::Object(default_map));
        }
        let jsonb = deser_res.unwrap();
        let mut words = Vec::new();
        let mut try_words = Vec::new();
        let level = jsonb
            .as_object()
            .unwrap()
            .get("level")
            .unwrap_or(&serde_json::Value::String("INFO".to_string()))
            .as_str()
            .unwrap()
            .to_string();
        for v in jsonb.as_object().unwrap().values() {
            try_words.push(v)
        }
        loop {
            let v = try_words.pop();
            if v.is_none() {
                break;
            }
            let try_str = v.unwrap().as_str();
            if try_str.is_some() {
                lazy_static! {
                    static ref RE: Regex = Regex::new(r"[\w]+([-_][\w]+)*").unwrap();
                };
                for cap in RE.captures_iter(try_str.unwrap()) {
                    words.push(cap.get(0).unwrap().as_str().to_string());
                }
                continue;
            }
            let try_nested = v.unwrap().as_object();
            if try_nested.is_some() {
                for k in try_nested.unwrap().keys() {
                    words.push(k.clone());
                }
                for val in try_nested.unwrap().values() {
                    try_words.push(val);
                }
            }
        }
        Self {
            time: chrono::offset::Utc::now(),
            shard: shard.clone(),
            data: jsonb,
            level: level,
            words: words,
        }
    }
}
pub struct MyConsumer {
    no_ack: bool,
    sender: mpsc::Sender<LogRow>,
    shard_counter: i32,
}

impl MyConsumer {
    /// Return a new consumer.
    ///
    /// See [Acknowledgement Modes](https://www.rabbitmq.com/consumers.html#acknowledgement-modes)
    ///
    /// no_ack = [`true`] means automatic ack and should NOT send ACK to server.
    ///
    /// no_ack = [`false`] means manual ack, and should send ACK message to server.
    pub fn new(no_ack: bool, sender: mpsc::Sender<LogRow>) -> Self {
        // Now we can execute a simple statement that just returns its parameter.
        Self {
            no_ack,
            sender,
            shard_counter: 0,
        }
    }
}

#[async_trait]
impl AsyncConsumer for MyConsumer {
    async fn consume(
        &mut self,
        channel: &Channel,
        deliver: Deliver,
        _basic_properties: BasicProperties,
        content: Vec<u8>,
    ) {
        let utf8_content = String::from_utf8(content).unwrap_or("{}".to_string());
        if deliver.delivery_tag() % 10000 == 0 {
            info!("consume delivery {} on channel {}", deliver, channel,);
        }
        let log = LogRow::new(&utf8_content.as_str(), &self.shard_counter);
        self.sender.send(log).await.unwrap();
        self.shard_counter = (self.shard_counter + 1) % 4;
        // ack explicitly if manual ack
        if !self.no_ack {
            info!("ack to delivery {} on channel {}", deliver, channel);
            let args = BasicAckArguments::new(deliver.delivery_tag(), false);
            channel.basic_ack(args).await.unwrap();
        }
    }
}

#[tokio::main(flavor = "multi_thread", worker_threads = 6)]
async fn main() {
    // construct a subscriber that prints formatted traces to stdout
    // global subscriber with log level according to RUST_LOG
    tracing_subscriber::registry()
        .with(fmt::layer())
        .with(
            EnvFilter::builder()
                .with_default_directive(metadata::LevelFilter::INFO.into())
                .from_env_lossy(),
        )
        .try_init()
        .ok();

    // open a connection to RabbitMQ server

    // open a channel on the connection
    // declare a server-named transient queue

    // bind the queue to exchange
    //let rounting_key = "amqprs.example";
    //let exchange_name = "amq.topic";

    // The connection object performs the actual communication with the database,
    // so spawn it off to run on its own.
    //////////////////////////////////////////////////////////////////////////////
    // start consumer, auto ack

    let (tx, mut rx) = mpsc::channel(4096);

    for _i in 0..4 {
        let tx2 = tx.clone();
        tokio::spawn(async move {
            let connection = amqpConnection::open(&OpenConnectionArguments::new(
                "localhost",
                5672,
                "guest",
                "guest",
            ))
            .await
            .unwrap();
            let channel = connection.open_channel(None).await.unwrap();
            let (queue_name, _, _) = channel
                //.queue_declare(QueueDeclareArguments::durable_client_named(
                //    "amqprs.examples.basic",
                //))
                .queue_declare(QueueDeclareArguments::default())
                .await
                .unwrap()
                .unwrap();
            channel
                .queue_bind(QueueBindArguments::new(
                    &queue_name,
                    "amq.topic",
                    "amqprs.example",
                ))
                .await
                .unwrap();
            let args = BasicConsumeArguments::new(&queue_name, "basic_consumer")
                .manual_ack(false)
                .finish();

            channel
                .basic_consume(MyConsumer::new(args.no_ack, tx2), args)
                .await
                .unwrap();
            let guard = Notify::new();
            guard.notified().await;
        });
    }

    let _manager = tokio::spawn(async move {
        // Establish a connection to the server
        let (mut client, db_connect) = connect("host=localhost user=postgres password=test", NoTls)
            .await
            .unwrap();
        tokio::spawn(async move {
            if let Err(e) = db_connect.await {
                eprintln!("connection error: {}", e);
            }
        });
        // Start receiving messages
        while let Some(cmd) = rx.recv().await {
            let mut rows = Vec::new();
            rows.push(cmd);
            for _i in 0..512 {
                let res = rx.try_recv();
                if res.is_err() {
                    break;
                }
                rows.push(res.unwrap());
            }
            let transaction = client.transaction().await.unwrap();
            let sink = transaction
                .copy_in("COPY logs (time, shard, logdata, level, words) FROM STDIN BINARY")
                .await
                .unwrap();
            let writer = BinaryCopyInWriter::new(
                sink,
                &[
                    Type::TIMESTAMPTZ,
                    Type::INT4,
                    Type::JSONB,
                    Type::TEXT,
                    Type::TEXT_ARRAY,
                ],
            );
            pin_mut!(writer);
            for log in rows {
                let mut row: Vec<&'_ (dyn ToSql + Sync)> = Vec::new();
                row.push(&log.time);
                row.push(&log.shard);
                row.push(&log.data);
                row.push(&log.level);
                row.push(&log.words);
                let _num_written = writer.as_mut().write(&row).await.unwrap();
            }
            writer.finish().await.unwrap();
            transaction.commit().await.unwrap();
        }
    });

    // consume forever
    info!("Consuming forever");
    let guard = Notify::new();
    guard.notified().await;
}
