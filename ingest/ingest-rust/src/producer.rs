use amqprs::{
    channel::{BasicPublishArguments, QueueBindArguments, QueueDeclareArguments},
    connection::{Connection, OpenConnectionArguments},
    BasicProperties,
};
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

use notify::{Config, RecommendedWatcher, RecursiveMode, Watcher};
use std::io::BufReader;
use std::path::Path;
use std::sync::mpsc::channel;
use std::time::Duration;
use std::{fs::File, io::BufRead};

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() {
    // construct a subscriber that prints formatted traces to stdout
    // global subscriber with log level according to RUST_LOG
    tracing_subscriber::registry()
        .with(fmt::layer())
        .with(EnvFilter::from_default_env())
        .try_init()
        .ok();

    // open a connection to RabbitMQ server
    let connection = Connection::open(&OpenConnectionArguments::new(
        "localhost",
        5672,
        "guest",
        "guest",
    ))
    .await
    .unwrap();

    // open a channel on the connection
    let amqp_channel = connection.open_channel(None).await.unwrap();

    // declare a durable queue
    let (queue_name, _, _) = amqp_channel
        .queue_declare(QueueDeclareArguments::durable_client_named(
            "amqprs.examples.basic",
        ))
        .await
        .unwrap()
        .unwrap();

    // bind the queue to exchange
    let rounting_key = "amqprs.example";
    let exchange_name = "amq.topic";
    amqp_channel
        .queue_bind(QueueBindArguments::new(
            &queue_name,
            exchange_name,
            rounting_key,
        ))
        .await
        .unwrap();

    let args = BasicPublishArguments::new(exchange_name, rounting_key);
    let (tx, rx) = channel();
    let config = Config::default().with_poll_interval(Duration::from_millis(1000));
    let mut watcher: RecommendedWatcher = Watcher::new(tx, config).unwrap();
    let path = Path::new("./test.log");
    watcher.watch(path, RecursiveMode::NonRecursive).unwrap();
    let mut reader = BufReader::new(File::open(path).unwrap());
    loop {
        loop {
            let mut buf_str: Vec<u8> = Vec::new();
            let read_bytes = reader.read_until("\n".as_bytes()[0], &mut buf_str);
            if read_bytes.is_err() {
                break;
            } else {
                let read_num = read_bytes.unwrap();
                if read_num <= 0 {
                    break;
                }
            }

            amqp_channel
                .basic_publish(BasicProperties::default(), buf_str, args.clone())
                .await
                .unwrap();
        }
        let _rx_bytes = rx.recv();
    }
    //////////////////////////////////////////////////////////////////////////////
    // publish messages
    /*
    for _ in 0..5000 {
        if let Ok(lines) = read_lines("./test.log") {
            // Consumes the iterator, returns an (Optional) String
            for line in lines {
                if let Ok(ip) = line {

                }
            }
        }
    }
    */

    // create arguments for basic_publish

    // keep the `channel` and `connection` object from dropping before pub/sub is done.
    // channel/connection will be closed when drop.
    // explicitly close
    /*
    amqp_channel.close().await.unwrap();
    connection.close().await.unwrap();
    */
}
