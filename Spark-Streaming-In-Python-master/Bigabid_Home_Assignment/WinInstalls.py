from pyspark.sql import SparkSession
from pyspark.sql.functions import expr

from lib.logger import Log4j
/*
"Wins" stream:
timestamp: string
user: string
app: string
cost: double
banner_id: string

"Installs" stream:
timestamp: string
user: string
banner_id: string
publisher_id: string
*/

if __name__ == "__main__":
    spark = SparkSession \
        .builder \
        .appName("File Streaming Demo") \
        .master("local[3]") \
        .config("spark.streaming.stopGracefullyOnShutdown", "true") \
        .config("spark.sql.streaming.schemaInference", "true") \
        .getOrCreate()

    logger = Log4j(spark)

    raw_df = spark.readStream \
        .format("json") \
        .option("path", "/Users/tamir.wainstain/src/Spark-Streaming-In-Python-master/02-FileStreamDemo/SampleData") \
        .option("maxFilesPerTrigger", 1) \
        .load()

    explode_df = raw_df.selectExpr("InvoiceNumber", "CreatedTime", "StoreID", "PosID",
                                   "CustomerType", "PaymentMethod", "DeliveryType", "DeliveryAddress.City",
                                   "DeliveryAddress.State",
                                   "DeliveryAddress.PinCode", "explode(InvoiceLineItems) as LineItem")

    flattened_df = explode_df \
        .withColumn("ItemCode", expr("LineItem.ItemCode")) \
        .withColumn("ItemDescription", expr("LineItem.ItemDescription")) \
        .withColumn("ItemPrice", expr("LineItem.ItemPrice")) \
        .withColumn("ItemQty", expr("LineItem.ItemQty")) \
        .withColumn("TotalValue", expr("LineItem.TotalValue")) \
        .drop("LineItem")

    #invoiceWriterQuery = flattened_df.writeStream \
    #i    .format("json") \
    #i    .queryName("Flattened Invoice Writer") \
    #i    .outputMode("append") \
    #i    .option("path", "output") \
    #i    .option("checkpointLocation", "chk-point-dir") \
    #i    .trigger(processingTime="10 Seconds") \
    #i    .start()

    invoiceWriterQuery = \
        flattened_df.writeStream \
        .format("console").outputMode("append")\
        .trigger(processingTime="10 Seconds")\
        .start()\

    logger.info("Flattened Invoice Writer started")
    invoiceWriterQuery.awaitTermination()

