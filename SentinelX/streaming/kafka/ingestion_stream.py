from confluent_kafka import Producer
import json
import time

class SatelliteIngestionStream:
    """
    Tactical Kafka Stream Producer.
    Streams Satellite Meta-Data and COG URLs to the processing cluster.
    """
    def __init__(self, bootstrap_servers="localhost:9092"):
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "client.id": "starshield-ingestor",
            "acks": "all",
            "retries": 5
        })

    def delivery_report(self, err, msg):
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def stream_product(self, product_metadata):
        """
        Produce a new satellite product event to Kafka.
        """
        # Key by AOI/Region for partition locality
        key = product_metadata.get("aoi_id", "global")
        
        self.producer.produce(
            "satellite-products",
            key=key,
            value=json.dumps(product_metadata),
            callback=self.delivery_report
        )
        self.producer.poll(0)

    def close(self):
        self.producer.flush()

if __name__ == "__main__":
    # Simulate Ingestion from AWS Ground Station
    ingestor = SatelliteIngestionStream()
    
    dummy_product = {
        "id": "S2A_MSIL2A_20231024T083951_N0509_R064_T36RXL_20231024T120150",
        "aoi_id": "36RXL",
        "timestamp": time.time(),
        "bands": ["B02", "B03", "B04", "B08", "SAR_VV", "SAR_VH"],
        "cog_url": "s3://sentinel-cogs/sentinel-2-l2a/36/R/XL/2023/10/24/0/COG.tif"
    }
    
    ingestor.stream_product(dummy_product)
    ingestor.close()
