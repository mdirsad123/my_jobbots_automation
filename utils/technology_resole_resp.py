# list top technologies used by aws data engineer
tech_roles_responsibilities = {
    "Python": {
        "subset": "Python",
        "bullet_points": [
            "Developed Python scripts to automate daily tasks and workflows.",
            "Built reusable Python modules to enhance code readability.",
            "Used Python lists and dicts for efficient data operations.",
            "Applied Python loops and conditions for data processing.",
            "Created flexible Python functions using *args and **kwargs.",
            "Handled CSV/JSON files using Python read/write functions.",
            "Wrote Python unit tests to validate function logic and output.",
            "Installed Python packages via pip, poetry and virtual environments.",
            "Wrote Python lambda and list, dict comprehensions for clean code.",
            "Built Python classes using OOP concepts like inheritance.",
            "Created command-line tools using Python and argparse.",
            "Used decorators and closures in Python for custom behavior.",
            "Applied regex with Python's re module to extract patterns.",
            "Used Git to version control and manage Python scripts.",
            "Worked with Python data types like int, str, list, and dict.",
            "Exeption handling in Python using try-except-finally blocks.",
            "Created Python generators with yield for memory efficiency.",
            "Implemented Python iterators to loop through custom objects."
        ]
    },
    "SQL": {
        "subset": "SQL",
        "bullet_points": [
            "Write optimized SQL queries for data analysis and transformation tasks.",
            "Implement advanced SQL techniques like window functions, CTEs, and subqueries.",
            "Create and manage SQL views, indexes, and stored procedures for efficient database operations.",
            "Debug and tune complex SQL joins and aggregations for performance optimization.",
            "Use SQL SELECT statements to extract data from tables.",
            "Perform SQL joins to combine data from multiple tables.",
            "Filter and sort data using SQL WHERE, ORDER BY, and LIMIT.",
            "Group and summarize data using SQL GROUP BY and HAVING.",
            "Insert, update, and delete records using SQL DML commands.",
            "Use SQL aliases to simplify column and table names.",
            "Create tables and define schema using SQL DDL commands.",
            "Write nested SQL queries for complex data retrieval.",
            "Validate data consistency with SQL constraints and keys.",
            "Work with NULL values and SQL COALESCE/ISNULL functions."
        ]
    },
    "EMR": {
        "subset": "",
        "bullet_points": [
            "Run distributed Spark and Hive jobs using Amazon EMR clusters.",
            "Optimize EMR costs via spot instances and autoscaling features.",
            "Integrate EMR with S3, DynamoDB, and HDFS for data access.",
            "Tune EMR cluster configs for better performance and reliability.",
            "Use EMRFS consistent view for reliable S3 data interactions."
        ]
    },
    "S3": {
        "subset": "AWS",
        "bullet_points": [
            "Design scalable data lakes using S3 for big data analytics.",
            "Implement S3 lifecycle policies to reduce storage cost.",
            "Secure S3 data using server-side encryption and IAM policies.",
            "Trigger workflows via S3 events linked to Lambda functions.",
            "Organize S3 data using partitions for faster query access."
        ]
    },
    "Redshift": {
        "subset": "AWS",
        "bullet_points": [
            "Design and optimize schemas and queries using Amazon Redshift.",
            "Use Redshift COPY to load and transform S3 data efficiently.",
            "Query external S3 data using Redshift Spectrum seamlessly.",
            "Monitor Redshift performance via system tables and CloudWatch.",
            "Secure Redshift data using IAM roles and encryption features."
        ]
    },
    "RDS": {
        "subset": "AWS",
        "bullet_points": [
            "Provision and manage MySQL/PostgreSQL instances using RDS.",
            "Automate backups, monitoring, and failover setup using RDS.",
            "Tune database parameters for better performance using RDS.",
            "Design ETL pipelines with RDS as source or target system.",
            "Implement read replicas for scaling read queries in RDS.",
            "Secure RDS access using IAM roles, VPC, and encryption.",
            "Monitor slow queries and optimize indexes using RDS logs.",
            "Schedule snapshot backups and retention policies via RDS.",
            "Use RDS parameter groups to control DB engine behavior.",
            "Enable multi-AZ deployment in RDS for high availability."
        ]
    },
    "DynamoDB": {
        "subset": "DynamoDB",
        "bullet_points": [
            "Model scalable NoSQL tables using partition keys in DynamoDB.",
            "Configure read/write capacity and autoscaling in DynamoDB.",
            "Use DynamoDB Streams with Lambda for real-time processing.",
            "Improve query speed using GSIs and LSIs in DynamoDB.",
            "Secure DynamoDB data using IAM roles and KMS encryption.",
            "Perform CRUD operations using AWS SDK with DynamoDB tables.",
            "Design access patterns and key structure in DynamoDB.",
            "Enable TTL in DynamoDB to auto-expire unused data items.",
            "Monitor DynamoDB metrics using CloudWatch dashboards.",
            "Use BatchWriteItem and BatchGetItem for bulk ops in DynamoDB."
        ]
    },
    "Aurora": {
        "subset": "DevOps",
        "bullet_points": [
            "Integrate with Lambda for data-driven application workflows using Aurora.",
            "Manage schema updates and migrations efficiently using Aurora.",
            "Secure Aurora databases with IAM, VPC, and SSL connections.",
            "Use read replicas in Aurora to scale read-heavy workloads easily.",
            "Optimize query performance with Aurora query plan insights.",
            "Schedule backups and snapshot retention policies using Aurora."
        ]
    },
    "MSK": {
        "subset": "MSK",
        "bullet_points": [
            "Ingest and stream real-time data using Kafka APIs with MSK.",
            "Configure secure MSK clusters with encryption and IAM roles.",
            "Monitor MSK broker health and consumer lag via CloudWatch.",
            "Use Kafka Connect on MSK to integrate external data sources.",
            "Process MSK streams using Spark, Flink, or AWS Lambda apps."
        ]
    },
    "Airflow": {
        "subset": "python",
        "bullet_points": [
            "Orchestrate data pipelines using DAGs and tasks in Airflow.",
            "Schedule and track jobs with logs and alerts using Airflow UI.",
            "Integrate AWS services like S3 and Redshift using Airflow hooks.",
            "Deploy DAGs securely on MWAA using managed Airflow services.",
            "Version and manage DAGs with Git for CI/CD in Airflow."
        ]
    },
    "DMS": {
        "subset": "AWS",
        "bullet_points": [
            "Migrate on-prem or cloud databases to AWS targets using DMS.",
            "Enable near real-time data replication with DMS tasks.",
            "Perform homogeneous or heterogeneous DB migrations using DMS.",
            "Monitor migration progress and logs via DMS dashboard.",
            "Apply transformation rules during data transfer using DMS."
        ]
    },
    "Snowball": {
        "subset": "DevOps",
        "bullet_points": [
            "Transfer large datasets to AWS securely using Snowball devices.",
            "Encrypt and move petabyte-scale data offline with Snowball.",
            "Integrate Snowball with on-prem storage for bulk data migration.",
            "Track Snowball job status and logs using AWS Console tools.",
            "Use Snowball Edge and CLI to automate data extraction tasks."
        ]
    },
    "Redshift Spectrum": {
        "subset": "AWS",
        "bullet_points": [
            "Query S3-based external tables using Redshift Spectrum SQL.",
            "Manage external schemas via Glue Catalog in Redshift Spectrum.",
            "Join S3 data with Redshift tables using Redshift Spectrum queries.",
            "Optimize Spectrum queries using Parquet or ORC file formats.",
            "Use Redshift Spectrum to query S3 without copying the data."
        ]
    },
    "Athena": {
        "subset": "AWS",
        "bullet_points": [
            "Query structured data in S3 using SQL with Amazon Athena.",
            "Use partitioning and projection to speed up Athena queries.",
            "Integrate Athena with Glue Catalog for schema management.",
            "Analyze CloudTrail and ALB logs stored in S3 using Athena.",
            "Run Athena queries via SDK or connect to BI tools easily."
        ]
    },
    "QuickSight": {
        "subset": "AWS",
        "bullet_points": [
            "Create dashboards on Redshift, S3, and RDS data using QuickSight.",
            "Apply row-level security and filters for users in QuickSight.",
            "Use QuickSight SPICE for fast, in-memory data analytics.",
            "Schedule report refreshes and email delivery via QuickSight.",
            "Control access to visuals using IAM and SSO in QuickSight."
        ]
    },
    "Java": {
        "subset": "Java",
        "bullet_points": [
            "Build backend services and Spark jobs on EMR using Java.",
            "Develop Kafka producers and consumers in Java for streaming.",
            "Write custom UDFs in Hive or Spark for data tasks using Java.",
            "Use Java SDKs to connect with AWS services and databases.",
            "Ensure performance using thread-safe design in Java code."
        ]
    },
    "HiveQL": {
        "subset": "AWS",
        "bullet_points": [
            "Query large datasets on EMR and S3 using HiveQL scripts.",
            "Create partitioned and bucketed tables for speed in HiveQL.",
            "Join and filter structured S3 data efficiently using HiveQL.",
            "Use SerDe and write custom UDFs for formats in HiveQL.",
            "Manage table schemas via Hive metastore using HiveQL."
        ]
    },
    "PySpark": {
        "subset": "PySpark",
        "bullet_points": [
            "Build ETL pipelines for batch and streaming using PySpark.",
            "Transform data using DataFrame and SQL APIs in PySpark.",
            "Read and write data from S3 and Glue Catalog using PySpark.",
            "Handle JSON and evolving schemas in semi-structured data using PySpark.",
            "Monitor job performance using Spark UI and logs in PySpark."
        ]
    },
    "Boto3": {
        "subset": "AWS",
        "bullet_points": [
            "Automate AWS resource management using Python and Boto3.",
            "Trigger Glue, Lambda, and S3 jobs programmatically with Boto3.",
            "Handle retries and exceptions effectively using Boto3 logic.",
            "Use Boto3 paginators to manage large AWS API responses.",
            "Integrate Boto3 scripts in CI/CD and data workflows easily."
        ]
    },
    "Shell script": {
        "subset": "Python",
        "bullet_points": [
            "Automate ETL workflows using Bash and Shell script.",
            "Trigger Spark or SQL jobs via CLI using Shell script.",
            "Manage cron jobs and scheduled tasks using Shell script.",
            "Monitor system resources and logs via Shell script tools.",
            "Write install and setup automation using Shell script."
        ]
    },
    "dbt": {
        "subset": "DevOps",
        "bullet_points": [
            "Build and manage SQL data models using dbt framework.",
            "Use Jinja and macros to create reusable logic in dbt.",
            "Track versioned, testable models with dbt and Git.",
            "Generate lineage and docs automatically using dbt.",
            "Run dbt models as part of CI/CD data pipelines."
        ]
    },
    "Spark Streaming": {
        "subset": "pyspark",
        "bullet_points": [
            "Stream real-time Kafka or Kinesis data using Spark Streaming.",
            "Use windowed operations and time-based joins in Spark Streaming.",
            "Write output to S3 or Redshift using Spark Streaming jobs.",
            "Maintain checkpoints for recovery using Spark Streaming.",
            "Optimize Spark Streaming memory and latency for efficiency."
        ]
    },
    "CloudWatch Logs": {
        "subset": "CloudWatch",
        "bullet_points": [
            "Centralize logs from Glue, Lambda, and apps using CloudWatch Logs.",
            "Set retention, filters, and alerts using CloudWatch Logs.",
            "Create log dashboards for visibility using CloudWatch Logs.",
            "Troubleshoot app issues with CloudWatch Logs and metrics.",
            "Enable cross-account access for shared CloudWatch Logs."
        ]
    },
    "CloudWatch Metrics": {
        "subset": "CloudWatch",
        "bullet_points": [
            "Track AWS metrics like CPU, memory, and I/O using CloudWatch Metrics.",
            "Set alarms for services like Lambda and Glue using CloudWatch Metrics.",
            "Create custom dashboards using CloudWatch Metrics insights.",
            "Use CloudWatch Metrics for auto-scaling and alerts.",
            "Connect CloudWatch Metrics with EventBridge for automation."
        ]
    },
    "X-Ray": {
        "subset": "AWS",
        "bullet_points": [
            "Trace distributed apps and Lambda flows using X-Ray.",
            "Find performance bottlenecks with AWS X-Ray traces.",
            "Visualize latency and call graphs using X-Ray UI.",
            "Correlate X-Ray traces with logs via request IDs.",
            "Add custom annotations to segments using X-Ray."
        ]
    },
    "SNS": {
        "subset": "AWS",
        "bullet_points": [
            "Send alerts via email, SMS, or Lambda using SNS topics.",
            "Use fan-out pattern to notify multiple targets with SNS.",
            "Trigger workflows based on event rules using SNS.",
            "Secure SNS topics with IAM and encryption settings.",
            "Connect SNS with CloudWatch and EventBridge alerts."
        ]
    },
    "IAM": {
      "subset": "AWS",
      "bullet_points": [
        "Define least-privilege access policies using IAM roles.",
        "Set up cross-service permissions and trust with IAM roles.",
        "Implement ABAC to control access dynamically using IAM.",
        "Audit and rotate credentials and access keys using IAM.",
        "Use IAM for federated access with external identity providers."
      ]
    },
    "KMS": {
      "subset": "AWS",
      "bullet_points": [
        "Encrypt data at rest in S3, RDS, and Redshift using KMS.",
        "Manage custom key policies and grants securely via KMS.",
        "Use envelope encryption for better performance with KMS.",
        "Track key usage and access audits using KMS + CloudTrail.",
        "Enable auto or manual key rotation in AWS using KMS."
      ]
    },
    "CloudTrail": {
      "subset": "AWS",
      "bullet_points": [
        "Track AWS API calls and user activity using CloudTrail.",
        "Create multi-region trails for full coverage in CloudTrail.",
        "Send CloudTrail logs to S3 and CloudWatch for analysis.",
        "Connect CloudTrail with GuardDuty for threat detection.",
        "Use CloudTrail logs for security audits and compliance."
      ]
    },
    "ECS": {
      "subset": "AWS",
      "bullet_points": [
        "Run containerized workloads using Fargate or EC2 in ECS.",
        "Manage task definitions and scaling policies in ECS.",
        "Use ALB for load balancing and discovery in ECS services.",
        "Assign IAM roles securely to ECS tasks and containers.",
        "Monitor ECS service health and metrics via CloudWatch."
      ]
    },
    "EKS": {
      "subset": "DevOps",
      "bullet_points": [
        "Deploy scalable Kubernetes workloads on AWS using EKS.",
        "Manage Helm charts and manifests for apps using EKS.",
        "Use Prometheus and Grafana for monitoring EKS clusters.",
        "Scale pods and nodes automatically in EKS environments.",
        "Secure workloads using IAM roles for service accounts in EKS."
      ]
    },
    "CDK": {
      "subset": "DevOps",
      "bullet_points": [
        "Define AWS infrastructure using code with CDK.",
        "Use CDK constructs to simplify reusable stack components.",
        "Deploy stacks via CI/CD pipelines using CDK integration.",
        "Test CDK code with unit assertions for infrastructure logic.",
        "Convert CDK code into CloudFormation templates easily."
      ]
    },
    "deployment": {
      "subset": "",
      "bullet_points": [
        "Define cloud infrastructure using IAC tools for deployment.",
        "Use reusable templates and parameterized stacks in deployment.",
        "Deploy resources via CI/CD with automation in deployment.",
        "Validate infrastructure changes before deployment.",
        "Manage updates and rollbacks using stack policies in deployment."
      ]
    },
    "SQL Server": {
      "subset": "SQL",
      "bullet_points": [
        "Design tables, views, and procedures using SQL Server.",
        "Use SSIS for ETL and data migrations with SQL Server.",
        "Optimize performance with indexes and partitions in SQL Server.",
        "Connect SQL Server to Glue or DMS for AWS integration.",
        "Schedule backups and jobs with SQL Server Agent."
      ]
    },
    "Oracle": {
      "subset": "Oracle",
      "bullet_points": [
        "Extract and transform data using SQL and PL/SQL in Oracle.",
        "Connect Oracle to AWS Glue using JDBC drivers.",
        "Create stored procedures and packages using Oracle PL/SQL.",
        "Secure Oracle DB with roles, grants, and permissions.",
        "Monitor performance with AWR and OEM in Oracle."
      ]
    },
    # list top technologies used by ai data engineer
    "TensorFlow": {
        "subset": "AI",
        "bullet_points": [
            "Build deep learning models for training and inference using TensorFlow.",
        "Train and tune neural networks on large datasets using TensorFlow.",
        "Deploy models to production using TensorFlow Serving or TF Lite.",
        "Optimize training with GPU/TPU support using TensorFlow tools.",
        "Use TensorFlow for computer vision, NLP, and time series tasks."
        ]
    },
    "PyTorch": {
        "subset": "AI",
        "bullet_points": [
            "Develop deep learning models for training and testing using PyTorch.",
            "Use PyTorch for fast prototyping with dynamic computation graphs.",
            "Train models on GPU using efficient APIs provided by PyTorch.",
            "Deploy production-ready ML pipelines using PyTorch modules.",
            "Apply PyTorch in vision, NLP, and time-series ML tasks."
        ]
    },
    "scikit-learn": {
        "subset": "data science",
        "bullet_points": [
            "Train ML models like SVM and random forest using scikit-learn.",
            "Build preprocessing pipelines and transformers using scikit-learn.",
            "Tune model hyperparameters with GridSearchCV in scikit-learn.",
            "Evaluate model accuracy and precision using scikit-learn tools.",
            "Use scikit-learn to deploy models in Python applications."
        ]
    },
    "Random Forest": {
        "subset": "machine learning",
        "bullet_points": [
            "Build robust classifiers using random forest in Python.",
            "Train random forest for feature-rich classification tasks.",
            "Use random forest to handle missing and noisy data cases.",
            "Evaluate random forest using accuracy and confusion matrix.",
            "Apply random forest for fraud and churn prediction models."
        ]
    },
    "XGBoost": {
        "subset": "",
        "bullet_points": [
            "Build tree-based models on tabular data using XGBoost.",
            "Use early stopping and CV to tune models in XGBoost.",
            "Handle class imbalance with scale_pos_weight in XGBoost.",
            "Export XGBoost models for APIs or batch inference tasks.",
            "Apply XGBoost in classification and ranking problems."
        ]
    },
    "Pandas": {
        "subset": "Pandas",
        "bullet_points": [
            "Clean, filter, and transform structured data using Pandas.",
            "Perform groupby and aggregation operations using Pandas.",
            "Read/write CSV, Excel, Parquet, and SQL files using Pandas.",
            "Handle missing values and data types efficiently using Pandas.",
            "Merge and join datasets for feature creation using Pandas.",
            "Use Pandas for time series resampling and rolling windows.",
            "Filter rows based on conditions and queries using Pandas.",
            "Convert columns and apply custom functions using Pandas.",
            "Use Pandas to explore data with head(), describe(), and info().",
            "Export processed data to files or databases using Pandas."
        ]
    },
    "NumPy": {
        "subset": "python",
        "bullet_points": [
            "Perform numerical computations with multi-dimensional arrays using NumPy.",
            "Use broadcasting and vectorized operations for speed using NumPy.",
            "Implement mathematical and statistical functions using NumPy.",
            "Support image, signal, and matrix processing using NumPy.",
            "Optimize memory usage in high-volume computations using NumPy.",
            "Create and manipulate arrays, matrices, and tensors using NumPy.",
            "Use NumPy to generate random numbers and distributions.",
            "Apply filtering, slicing, and reshaping techniques using NumPy.",
            "Perform linear algebra operations and decompositions using NumPy.",
            "Use NumPy arrays for data preprocessing in ML workflows."
        ]
    },
    "Polars": {
        "subset": "Python",
        "bullet_points": [
        "Run fast DataFrame operations on large data using Polars.",
        "Use lazy execution and parallelism with Polars for ETL.",
        "Join, filter, and group data quickly using Polars engine.",
        "Replace Pandas in memory-heavy tasks using Polars.",
        "Read/write Parquet and Arrow formats efficiently using Polars."
        ]
    },
    "ONNX": {
        "subset": "ML",
        "bullet_points": [
        "Convert models to ONNX from PyTorch, TensorFlow, or sklearn.",
        "Deploy small, fast inference models cross-platform using ONNX.",
        "Speed up serving with ONNX Runtime in production APIs.",
        "Use ONNX to bridge training and serving model formats.",
        "Lower model latency and size for inference using ONNX."
        ]
    },
    "TorchScript": {
        "subset": "PyTorch",
        "bullet_points": [
        "Export PyTorch models to TorchScript for deployment tasks.",
        "Run model inference in Python or C++ using TorchScript.",
        "Integrate TorchScript models with APIs or custom logic.",
        "Use TorchScript to boost model execution speed.",
        "Test and debug scripted models before production with TorchScript."
        ]
    },
    "Flask": {
        "subset": "Flask",
        "bullet_points": [
            "Develop lightweight APIs for ML or data tasks using Flask.",
            "Create dashboards and UI endpoints quickly using Flask.",
            "Deploy Flask apps on cloud services like EC2 and ECS.",
            "Use Flask with Gunicorn or uWSGI for production scaling.",
            "Organize code with Flask Blueprints and middleware.",
            "Build RESTful routes and handle JSON data using Flask.",
            "Connect Flask to databases using SQLAlchemy or ORM tools.",
            "Add user auth and session handling in apps using Flask.",
            "Use Flask-CORS to manage cross-origin requests easily.",
            "Test Flask APIs with tools like Postman or Pytest."
        ]
    },
    "Dask": {
        "subset": "DevOps",
        "bullet_points": [
            "Parallelize Pandas-style workflows across multiple cores or machines using Dask.",
            "Scale data processing on large datasets that exceed memory using Dask.",
            "Create custom DAGs for complex data workflows using Dask.",
            "Deploy distributed computations and monitor via dashboard using Dask.",
            "Integrate with ML libraries like XGBoost and scikit-learn for training using Dask."
        ]
    },
    "Kafka": {
        "subset": "AWS",
        "bullet_points": [
            "Ingest and buffer high-throughput real-time messages using Kafka.",
            "Consume and transform streaming events from multiple sources using Kafka.",
            "Manage topics, partitions, and replication for scalability using Kafka.",
            "Stream processing with Kafka Streams or ksqlDB using Kafka.",
            "Secure streaming pipeline using IAM, SSL, and SASL with Kafka."
        ]
    },
    "Apache Flink": {
        "subset": "AWS",
        "bullet_points": [
            "Build low-latency real-time stream processing jobs using Apache Flink.",
            "Use watermarks and event-time semantics for accuracy using Apache Flink.",
            "Manage application state with savepoints and checkpoints using Apache Flink.",
            "Integrate with Kafka, S3, and Kinesis for input/output using Apache Flink.",
            "Monitor pipelines and fault tolerance via Flink Dashboard using Apache Flink."
        ]
    },
    "Kinesis": {
        "subset": "AWS",
        "bullet_points": [
            "Ingest and store real-time events for analytics and ML using Kinesis.",
            "Process and route events with Kinesis Data Analytics and Firehose using Kinesis.",
            "Enable high throughput ingestion by scaling shards dynamically using Kinesis.",
            "Implement Lambda consumers and custom apps for real-time use cases using Kinesis.",
            "Use enhanced fan-out for parallel data consumption using Kinesis."
        ]
    },
    "Feast": {
        "subset": "AWS",
        "bullet_points": [
            "Manage and serve ML features efficiently for online/offline use using Feast.",
            "Materialize batch features into data warehouse stores using Feast.",
            "Provide real-time access to features for model inference using Feast.",
            "Track lineage and monitor usage of features using Feast.",
            "Integrate with Redis, BigQuery, and S3 for storage using Feast."
        ]
    },
    "Tecton": {
        "subset": "DevOps",
        "bullet_points": [
            "Create and deploy production-ready feature pipelines using Tecton.",
            "Maintain feature freshness with streaming or scheduled updates using Tecton.",
            "Use declarative definitions for reusable ML features using Tecton.",
            "Integrate Tecton with ML model deployments like SageMaker using Tecton.",
            "Facilitate ML collaboration and governance using Tecton."
        ]
    },
    "SageMaker Feature Store": {
        "subset": "DevOps",
        "bullet_points": [
            "Create and manage feature groups for training/inference using SageMaker Feature Store.",
            "Serve low-latency features to ML endpoints using SageMaker Feature Store.",
            "Maintain consistency across training and production pipelines using SageMaker Feature Store.",
            "Track feature access, drift, and history using SageMaker Feature Store.",
            "Secure feature data with IAM and encryption using SageMaker Feature Store."
        ]
    },
    "Azure ML": {
        "subset": "Azure",
        "bullet_points": [
            "Train and deploy machine learning models at scale using Azure ML.",
            "Use AutoML and hyperparameter tuning for faster results using Azure ML.",
            "Create reproducible training workflows with pipelines using Azure ML.",
            "Deploy models as endpoints with autoscaling and monitoring using Azure ML.",
            "Integrate Azure ML with DevOps CI/CD for continuous training."
        ]
    },
    "Data Factory": {
        "subset": "AWS",
        "bullet_points": [
            "Create and orchestrate data pipelines across cloud/on-prem using Data Factory.",
            "Schedule and monitor ETL workflows using Data Factory.",
            "Move and transform data from structured and unstructured sources using Data Factory.",
            "Trigger Azure ML and Databricks jobs from pipelines using Data Factory.",
            "Visualize pipeline status with built-in monitoring dashboards using Data Factory."
        ]
    },
    "Data Lake": {
        "subset": "",
        "bullet_points": [
            "Store raw, curated, and processed datasets at scale using Data Lake.",
            "Enable schema evolution and partitioning for performance using Data Lake.",
            "Secure access with IAM, encryption, and audit logs using Data Lake.",
            "Support parallel reads and analytics with Spark or Presto using Data Lake.",
            "Apply versioning and lifecycle policies to manage cost using Data Lake."
        ]
    },
    "Vertex AI": {
        "subset": "AI",
        "bullet_points": [
            "Train and deploy ML models using AutoML or custom pipelines using key Vertex AI.",
            "Build reproducible ML workflows with pipeline orchestration using key Vertex AI.",
            "Serve models via endpoints or batch prediction jobs using key Vertex AI.",
            "Monitor model performance and data drift in production using key Vertex AI.",
            "Integrate with BigQuery, Dataflow, and GCS pipelines using key Vertex AI."
        ]
    },

    "BigQuery": {
        "subset": "DevOps",
        "bullet_points": [
            "Query petabyte-scale datasets using SQL without managing infrastructure using key BigQuery.",
            "Join and analyze data across GCS, Bigtable, and external sources using key BigQuery.",
            "Create scheduled queries and materialized views for reports using key BigQuery.",
            "Connect BigQuery to BI dashboards or ML models using key BigQuery.",
            "Secure access with IAM and apply row-level permissions using key BigQuery."
        ]
    },

    "Dataflow": {
        "subset": "",
        "bullet_points": [
            "Create batch and streaming data pipelines with Apache Beam using key Dataflow.",
            "Handle windowing, event-time processing, and watermarking using key Dataflow.",
            "Deploy reusable jobs with parameterized templates using key Dataflow.",
            "Auto-scale pipelines based on workload and input size using key Dataflow.",
            "Track pipeline health and metrics using Dataflow UI using key Dataflow."
        ]
    },

    "Cloud Functions": {
        "subset": "",
        "bullet_points": [
            "Trigger serverless functions on events like file uploads or Pub/Sub using key Cloud Functions.",
            "Integrate APIs, ML models, and Firestore for lightweight compute using key Cloud Functions.",
            "Handle short ETL tasks and pre/post-processing steps using key Cloud Functions.",
            "Secure with IAM and isolate environments per function using key Cloud Functions.",
            "Monitor function logs and errors using Cloud Logging using key Cloud Functions."
        ]
    },

    "Delta Lake": {
        "subset": "DevOps",
        "bullet_points": [
            "Maintain ACID compliance in data lakes for updates and deletes using key Delta Lake.",
            "Use time travel for versioned access to data history using key Delta Lake.",
            "Support schema evolution and audit trails in pipelines using key Delta Lake.",
            "Optimize performance with Z-ordering and compaction using key Delta Lake.",
            "Integrate seamlessly with Apache Spark jobs using key Delta Lake."
        ]
    },

    "Apache Hudi": {
        "subset": "DevOps",
        "bullet_points": [
            "Enable upserts and incremental loads in data lakes using key Apache Hudi.",
            "Stream CDC and real-time events into storage using key Apache Hudi.",
            "Roll back or recover datasets with commit-based lineage using key Apache Hudi.",
            "Ingest into S3 or GCS with Spark or Flink engines using key Apache Hudi.",
            "Query datasets with Presto, Hive, or Trino engines using key Apache Hudi."
        ]
    },

    "Iceberg": {
        "subset": "DevOps",
        "bullet_points": [
            "Manage large tables with schema evolution and partitioning using key Iceberg.",
            "Enable ACID operations and table snapshots on data lakes using key Iceberg.",
            "Write and update data via Spark, Flink, or Hive using key Iceberg.",
            "Query efficiently with Athena, Presto, or Trino using key Iceberg.",
            "Optimize performance via metadata caching and pruning using key Iceberg."
        ]
    },

    "Snowflake": {
        "subset": "Snowflake",
        "bullet_points": [
            "Run scalable SQL queries on structured and semi-structured data using key Snowflake.",
            "Perform data transformation directly in the warehouse using key Snowflake.",
            "Use Snowpipe for near real-time ingestion from streams using key Snowflake.",
            "Share secure data across accounts and clouds using key Snowflake.",
            "Apply access control, masking, and roles for data governance using key Snowflake."
        ]
    },

    "Presto": {
        "subset": "DevOps",
        "bullet_points": [
            "Query S3, HDFS, or Hive data directly without ingestion using key Presto.",
            "Join datasets across sources like MySQL, Kafka, and Hive using key Presto.",
            "Perform interactive ad-hoc analysis using ANSI SQL using key Presto.",
            "Leverage Hive metastore for schema resolution using key Presto.",
            "Support reporting dashboards and large-scale queries using key Presto."
        ]
    },

    "dbt": {
        "subset": "DevOps",
        "bullet_points": [
            "Write modular SQL models to transform raw data in key dbt pipelines.",
            "Add version control, tests, and documentation for key dbt models.",
            "Auto-generate lineage graphs and catalogs using key dbt CLI or UI.",
            "Run data transformations in CI/CD pipelines using key dbt Cloud or Core.",
            "Manage dev, staging, and prod environments via configs in key dbt."
        ]
    },

    "Dagster": {
        "subset": "AWS",
        "bullet_points": [
            "Build modular and type-safe ETL pipelines using key Dagster framework.",
            "Track metadata and lineage of data assets with key Dagster tooling.",
            "Monitor job runs, errors, and logs via key Dagster UI or CLI.",
            "Deploy pipelines on ECS, Kubernetes, or Docker using key Dagster.",
            "Integrate with Airbyte, dbt, and Snowflake in key Dagster workflows."
        ]
    },

    "Glue": {
        "subset": "AWS",
        "bullet_points": [
            "Create scalable ETL jobs using PySpark or Python Shell in key Glue.",
            "Auto-discover schema from S3 or JDBC using key Glue Crawlers.",
            "Chain multiple jobs using Workflows and Triggers in key Glue.",
            "Connect to Redshift, S3, RDS, or DynamoDB via key Glue jobs.",
            "Improve performance with partitioning and bookmarks in key Glue."
        ]
    },

    "Step Functions": {
        "subset": "AWS",
        "bullet_points": [
            "Orchestrate serverless workflows across Lambda, Glue, SageMaker using key Step Functions.",
            "Add retries, timeouts, and parallel steps in state machines using key Step Functions.",
            "Monitor run history and metrics in AWS Console with key Step Functions.",
            "Secure workflows using IAM roles and policies in key Step Functions.",
            "Trigger event-driven workflows from API Gateway or EventBridge using key Step Functions."
        ]
    },
    # list top technologies used by python developer
    "pip": {
        "subset": "Python",
        "bullet_points": [
            "Install and manage Python libraries efficiently using pip.",
            "Freeze and share dependencies with `requirements.txt` using pip.",
            "Resolve and debug package conflicts using pip.",
            "Automate dependency setup in CI/CD pipelines using pip.",
            "Audit and upgrade packages to fix vulnerabilities using pip."
        ]
    },
    "Poetry": {
        "subset": "Python",
        "bullet_points": [
            "Manage project dependencies and environments seamlessly using Poetry.",
            "Define metadata and scripts via `pyproject.toml` using Poetry.",
            "Publish packages to PyPI or private registries using Poetry.",
            "Ensure reproducible builds using `poetry.lock` using Poetry.",
            "Use Poetry in CI/CD for reliable installs and versioning using Poetry."
        ]
    },
    "pipenv": {
        "subset": "Python",
        "bullet_points": [
            "Create isolated environments using Pipfile and Pipfile.lock using pipenv.",
            "Automatically resolve and lock dependencies using pipenv.",
            "Switch Python versions flexibly within a project using pipenv.",
            "Audit for known security issues in dependencies using pipenv.",
            "Use pipenv in CI workflows for consistent environments using pipenv."
        ]
    },
    "conda": {
        "subset": "DevOps",
        "bullet_points": [
            "Create cross-language environments for ML and analytics using conda.",
            "Install and manage scientific packages with optimized binaries using conda.",
            "Export and reproduce environments via `environment.yml` using conda.",
            "Manage native dependencies and versions efficiently using conda.",
            "Quickly switch between multiple environments across projects using conda."
        ]
    },
    "venv": {
        "subset": "DevOps",
        "bullet_points": [
            "Create isolated Python environments using venv.",
            "Activate project-specific environments for clean setups using venv.",
            "Prevent dependency conflicts across projects using venv.",
            "Use venv as a lightweight tool bundled with Python using venv.",
            "Support local development workflows without external tools using venv."
        ]
    },
    "virtualenv": {
        "subset": "DevOps",
        "bullet_points": [
            "Create isolated environments across Python versions using virtualenv.",
            "Support reusable shell scripts for environment setup using virtualenv.",
            "Speed up environment creation compared to venv using virtualenv.",
            "Use with virtualenvwrapper for advanced workflows using virtualenv.",
            "Ensure compatibility across legacy and modern Python tools using virtualenv."
        ]
    },
    "Django": {
        "subset": "Django",
        "bullet_points": [
            "Build full-stack web apps using built-in ORM, views, and templates using Django.",
            "Develop secure REST APIs with Django REST Framework using Django.",
            "Use Django Admin for CRUD and internal tooling using Django.",
            "Manage data models and schema changes via migrations using Django.",
            "Implement authentication and permissions with built-in support using Django."
        ]
    },
    "FastAPI": {
        "subset": "FastAPI",
        "bullet_points": [
            "Develop async REST APIs with auto-generated Swagger UI using FastAPI.",
            "Validate inputs and outputs with Pydantic models using FastAPI.",
            "Implement secure OAuth2/JWT authentication using FastAPI.",
            "Deploy apps with Uvicorn and Docker in production using FastAPI.",
            "Run background tasks and integrate with DBs and queues using FastAPI."
        ]
    },
    "Flask": {
        "subset": "Flask",
        "bullet_points": [
            "Develop lightweight web APIs and services using Flask.",
            "Create modular routes using Blueprints and Flask-Restful using Flask.",
            "Integrate SQLAlchemy for ORM and database operations using Flask.",
            "Deploy on cloud platforms like Heroku and AWS using Flask.",
            "Add sessions, templates, and middleware support using Flask."
        ]
    },
    "Jinja2": {
        "subset": "Django",
        "bullet_points": [
            "Render dynamic HTML templates in Flask, Django, or FastAPI using Jinja2.",
            "Use template inheritance with blocks and macros using Jinja2.",
            "Control logic with conditions and loops in templates using Jinja2.",
            "Ensure security by escaping user content using Jinja2.",
            "Build reusable UI components with templating features using Jinja2."
        ]
    },
    "Mako": {
        "subset": "Python",
        "bullet_points": [
            "Render templates with embedded Python expressions using Mako.",
            "Support advanced logic in templates for web apps using Mako.",
            "Use template inheritance and custom filters using Mako.",
            "Integrate with Pyramid and SQLAlchemy-based apps using Mako.",
            "Generate dynamic HTML for data dashboards using Mako."
        ]
    },
    "React": {
        "subset": "React",
        "bullet_points": [
            "Build dynamic single-page applications with component architecture using React.",
            "Consume APIs from Django or Flask backends using React.",
            "Use state management libraries like Redux or Context API using React.",
            "Integrate with routing, forms, and UI libraries using React.",
            "Optimize performance with memoization and lazy loading using React."
        ]
    },
    "Vue": {
        "subset": "Vue",
        "bullet_points": [
            "Create interactive UIs and SPAs with component-based design using Vue.",
            "Consume REST APIs from Django/FastAPI backends using Vue.",
            "Use Vue CLI or Vite for local dev and builds using Vue.",
            "Manage global state using Vuex or Pinia using Vue.",
            "Support real-time updates with WebSockets and Django Channels using Vue."
        ]
    },
    "HTMX": {
        "subset": "JavaScript",
        "bullet_points": [
            "Add interactivity to server-rendered HTML with minimal JS using HTMX.",
            "Use HTML attributes to bind backend endpoints to frontend events using HTMX.",
            "Enable AJAX form submissions and updates using HTMX.",
            "Simplify UI features like pagination and modals using HTMX.",
            "Rapidly prototype reactive interfaces with Django or Flask using HTMX."
        ]
    },
    "JWT": {
        "subset": "JWT",
        "bullet_points": [
            "Secure RESTful APIs through stateless token-based auth using JWT.",
            "Handle token expiration, refresh, and revocation securely using JWT.",
            "Implement user roles, scopes, and permissions inside access tokens using JWT.",
            "Integrate with OAuth2 flows for Google, GitHub logins using JWT.",
            "Use libraries like Authlib, PyJWT, or FastAPI JWT Bearer using JWT."
        ]
    },
    "OAuth": {
        "subset": "JWT",
        "bullet_points": [
            "Authenticate users with external identity providers using OAuth.",
            "Implement OAuth 2.0 flows for login with Google, GitHub, etc. using OAuth.",
            "Manage access tokens, refresh tokens, and scopes securely using OAuth.",
            "Integrate OAuth into APIs with FastAPI, Django, or Flask using OAuth.",
            "Use standard libraries like Authlib and Allauth for rapid setup using OAuth."
        ]
    },
    "BeautifulSoup": {
        "subset": "Python",
        "bullet_points": [
            "Parse and navigate HTML/XML documents using BeautifulSoup.",
            "Extract tags, attributes, and structured data for scraping using BeautifulSoup.",
            "Combine with requests or Selenium for complete scraping workflows using BeautifulSoup.",
            "Clean and format raw web content before storage using BeautifulSoup.",
            "Handle broken or nested HTML with various built-in parsers using BeautifulSoup."
        ]
    },
    "Selenium": {
        "subset": "Python",
        "bullet_points": [
            "Automate browsers for scraping, testing, or interaction using Selenium.",
            "Click buttons, fill forms, and simulate user input using Selenium.",
            "Handle dynamic JavaScript-rendered pages reliably using Selenium.",
            "Take screenshots or collect logs for debugging using Selenium.",
            "Run browser tests in headless mode with Chrome or Firefox using Selenium."
        ]
    },
    "Scrapy": {
        "subset": "Python",
        "bullet_points": [
            "Build scalable, event-driven web crawlers using Scrapy.",
            "Extract and clean structured data with pipelines using Scrapy.",
            "Export data to JSON, CSV, or databases using Scrapy.",
            "Throttle requests and rotate user agents/middleware using Scrapy.",
            "Integrate Selenium for hybrid dynamic scraping tasks using Scrapy."
        ]
    },
    "Playwright": {
        "subset": "DevOps",
        "bullet_points": [
            "Automate cross-browser interactions and testing using Playwright.",
            "Scrape JavaScript-heavy pages with fast execution using Playwright.",
            "Simulate user actions and page navigation programmatically using Playwright.",
            "Run headless browser tests in CI/CD pipelines using Playwright.",
            "Capture screenshots, traces, and logs for debugging using Playwright."
        ]
    },
    "Python scripts": {
        "subset": "Python",
        "bullet_points": [
            "Automate repetitive tasks like file processing or cleanup using Python scripts.",
            "Connect to APIs, databases, or external tools for automation using Python scripts.",
            "Schedule tasks using cron or Task Scheduler with logging using Python scripts.",
            "Write modular scripts with CLI and error handling using Python scripts.",
            "Send email reports or alerts from automation flows using Python scripts."
        ]
    },
    "APScheduler": {
        "subset": "Python",
        "bullet_points": [
            "Schedule Python jobs with cron, interval, or date triggers using APScheduler.",
            "Run background jobs in threads or processes using APScheduler.",
            "Integrate with Flask, FastAPI, or standalone scripts using APScheduler.",
            "Persist job state in memory, SQLite, or Redis backends using APScheduler.",
            "Use decorators to register functions as scheduled tasks using APScheduler."
        ]
    },
    "Celery": {
        "subset": "FastAPI",
        "bullet_points": [
            "Execute asynchronous tasks across distributed workers using Celery.",
            "Use Redis or RabbitMQ as a message broker backend using Celery.",
            "Handle retries, task chaining, and error recovery gracefully using Celery.",
            "Monitor job status and failures via Flower dashboard using Celery.",
            "Integrate easily with Django, Flask, or FastAPI apps using Celery."
        ]
    },
    "os": {
        "subset": "python",
        "bullet_points": [
            "Perform OS-level tasks like listing directories and handling paths using os.",
            "Manage environment variables and read/write system settings using os.",
            "Execute shell commands with subprocess or system calls using os.",
            "Get process-related info like PID, CPU, and memory details using os.",
            "Create, remove, or rename directories and files using os."
        ]
    },
    "shutil": {
        "subset": "Python",
        "bullet_points": [
            "Copy, move, and delete files or directories reliably using shutil.",
            "Create compressed archives (zip/tar) for backup or transfer using shutil.",
            "Recursively copy folder contents while preserving structure using shutil.",
            "Check and handle disk usage or free space with `shutil.disk_usage()` using shutil.",
            "Preserve file metadata like permissions or timestamps during copy using shutil."
        ]
    },
    "pathlib": {
        "subset": "Python",
        "bullet_points": [
            "Work with filesystem paths in an object-oriented way using pathlib.",
            "Join, resolve, and normalize file paths across platforms using pathlib.",
            "Check file existence, file type, and size using pathlib.",
            "Read and write file content with `Path.read_text()` or `write_text()` using pathlib.",
            "Easily iterate over directory contents with `Path.iterdir()` using pathlib."
        ]
    },
    "matplotlib": {
        "subset": "Python",
        "bullet_points": [
            "Create static plots, bar charts, and line graphs using matplotlib.",
            "Customize titles, labels, legends, and styles using matplotlib.",
            "Visualize trends, comparisons, and distributions using matplotlib.",
            "Save plots to PNG, PDF, or SVG formats using matplotlib.",
            "Integrate with pandas and NumPy for quick plotting using matplotlib."
        ]
    },
    "seaborn": {
        "subset": "Python",
        "bullet_points": [
            "Create statistical plots like bar, box, and violin charts using seaborn.",
            "Visualize trends, distributions, and correlations in datasets using seaborn.",
            "Generate heatmaps, pair plots, and count plots for EDA using seaborn.",
            "Customize color palettes and themes for better visuals using seaborn.",
            "Integrate with pandas DataFrames for quick plotting using seaborn."
        ]
    },
    "Plotly": {
        "subset": "Python",
        "bullet_points": [
            "Create static and interactive plots for data visualization using Plotly.",
            "Build dashboards with interactive charts and graphs using Plotly.",
            "Integrate Plotly visualizations into web applications using Plotly.",
            "Visualize time series, scatter plots, and 3D charts using Plotly.",
            "Customize tooltips, hover actions, and themes for better UX using Plotly."
        ]
    },
    "Bokeh": {
        "subset": "DevOps",
        "bullet_points": [
            "Create interactive dashboards and charts for analytics using Bokeh.",
            "Visualize large or streaming datasets in real-time using Bokeh.",
            "Embed Bokeh plots into Flask or Django web apps using Bokeh.",
            "Customize tooltips, zoom, and pan features easily using Bokeh.",
            "Deploy data dashboards via Bokeh Server or standalone HTML using Bokeh."
        ]
    },
    "PyTorch": {
        "subset": "AI",
        "bullet_points": [
            "Build and train deep learning models with flexibility using PyTorch.",
            "Use dynamic computation graphs for research workflows using PyTorch.",
            "Accelerate training using GPU support and CUDA integration using PyTorch.",
            "Leverage torchvision and torchaudio for image/audio tasks using PyTorch.",
            "Deploy production models with TorchScript or ONNX using PyTorch."
        ]
    },
    "TensorFlow": {
        "subset": "AI",
        "bullet_points": [
            "Design and train neural networks for various tasks using TensorFlow.",
            "Use Keras API for rapid prototyping and experimentation using TensorFlow.",
            "Deploy models with TensorFlow Serving and TensorFlow Lite using TensorFlow.",
            "Utilize distributed training strategies for large models using TensorFlow.",
            "Monitor performance using TensorBoard for real-time insights using TensorFlow."
        ]
    },
    "SQLAlchemy": {
        "subset": "Python",
        "bullet_points": [
            "Perform ORM-based queries for SQL databases using SQLAlchemy.",
            "Define models and relationships with declarative syntax using SQLAlchemy.",
            "Handle migrations with Alembic integration using SQLAlchemy.",
            "Integrate with Flask or FastAPI for backend APIs using SQLAlchemy.",
            "Write raw SQL for complex use cases when needed using SQLAlchemy."
        ]
    },
    "ORM": {
        "subset": "ORM",
        "bullet_points": [
            "Perform CRUD operations with Django models using Django ORM.",
            "Handle database schema changes with migrations using Django ORM.",
            "Write complex queries using QuerySet chaining using Django ORM.",
            "Integrate models into admin, views, and serializers using Django ORM.",
            "Optimize performance with select_related and prefetch_related using Django ORM."
        ]
    },
    "Django ORM": {
        "subset": "ORM",
        "bullet_points": [
            "Perform CRUD operations with Django models using Django ORM.",
            "Handle database schema changes with migrations using Django ORM.",
            "Write complex queries using QuerySet chaining using Django ORM.",
            "Integrate models into admin, views, and serializers using Django ORM.",
            "Optimize performance with select_related and prefetch_related using Django ORM."
        ]
    },
    "Tortoise ORM": {
        "subset": "ORM",
        "bullet_points": [
            "Define async ORM models and relationships for SQL databases using Tortoise ORM.",
            "Integrate with FastAPI for fully async backend operations using Tortoise ORM.",
            "Perform CRUD operations efficiently with awaitable methods using Tortoise ORM.",
            "Generate schemas from models for DB migrations using Tortoise ORM.",
            "Use SQLite, PostgreSQL, or MySQL backends seamlessly using Tortoise ORM."
        ]
    },
    "flake8": {
        "subset": "DevOps",
        "bullet_points": [
            "Enforce Python style rules and PEP8 compliance using flake8.",
            "Detect unused variables, imports, and indentation issues using flake8.",
            "Run flake8 in CI pipelines to maintain clean codebases using flake8.",
            "Combine with pre-commit hooks for automatic lint checks using flake8.",
            "Customize rules using configuration files (e.g., .flake8) using flake8."
        ]
    },
    "pylint": {
        "subset": "DevOps",
        "bullet_points": [
            "Perform static code analysis with detailed scores using pylint.",
            "Catch logical and stylistic issues during development using pylint.",
            "Use pylint plugins for Django, Flask, or type hints using pylint.",
            "Integrate with IDEs and CI/CD workflows for automation using pylint.",
            "Enforce naming conventions and docstring checks using pylint."
        ]
    },
    "black": {
        "subset": "DevOps",
        "bullet_points": [
            "Auto-format Python code with opinionated PEP8 rules using black.",
            "Ensure consistent code formatting across teams using black.",
            "Integrate with Git hooks or CI for code standardization using black.",
            "Combine with isort and flake8 for full code quality enforcement using black.",
            "Minimize code review nitpicks by automating style using black."
        ]
    },
    "isort": {
        "subset": "DevOps",
        "bullet_points": [
            "Sort and group Python imports consistently using isort.",
            "Prevent merge conflicts from unordered imports using isort.",
            "Integrate with black for seamless formatting pipelines using isort.",
            "Use config options to define custom sorting logic using isort.",
            "Run automatically via pre-commit or IDE plugins using isort."
        ]
    },
    "autopep8": {
        "subset": "DevOps",
        "bullet_points": [
            "Fix Python code style issues automatically using autopep8.",
            "Format large legacy codebases with minimal manual changes using autopep8.",
            "Integrate with text editors for real-time PEP8 fixes using autopep8.",
            "Support line-by-line or full-file formatting using autopep8.",
            "Use alongside flake8 for fix-and-check workflows using autopep8."
        ]
    },
    "mypy": {
        "subset": "DevOps",
        "bullet_points": [
            "Add static type checking for Python functions and variables using mypy.",
            "Catch type mismatches and invalid operations early using mypy.",
            "Ensure safety and maintainability in large projects using mypy.",
            "Annotate code using Python 3 type hints and validate using mypy.",
            "Integrate with CI to enforce type safety in PRs using mypy."
        ]
    },
    "pyright": {
        "subset": "DevOps",
        "bullet_points": [
            "Run fast static type checks with minimal config using pyright.",
            "Catch errors and improve code safety with type annotations using pyright.",
            "Use with VSCode for real-time feedback on types using pyright.",
            "Validate large Python projects with strong typing using pyright.",
            "Enable strict or lenient checking modes for gradual adoption using pyright."
        ]
    },
    "Docker": {
        "subset": "Docker",
        "bullet_points": [
            "Containerize Python and ML apps for consistent deployment using Docker.",
            "Write Dockerfiles to define base image, dependencies, and commands using Docker.",
            "Build, run, and debug isolated containers using Docker CLI using Docker.",
            "Push images to Docker Hub or ECR for reuse using Docker.",
            "Ensure dev/prod parity with local container testing using Docker."
        ]
    },
    "Docker Compose": {
        "subset": "Docker",
        "bullet_points": [
            "Define multi-container apps (e.g., web, db, cache) using Docker Compose.",
            "Use YAML to configure services, volumes, and networks using Docker Compose.",
            "Spin up full stacks with a single `docker-compose up` using Docker Compose.",
            "Override settings for different environments via `.env` files using Docker Compose.",
            "Run local dev environments with hot reloading support using Docker Compose."
        ]
    },
    "Lambda": {
        "subset": "AWS",
        "bullet_points": [
            "Run Python code without provisioning servers using Lambda.",
            "Trigger Lambda from S3, API Gateway, or CloudWatch events using Lambda.",
            "Write stateless functions for microservice tasks using Lambda.",
            "Use environment variables and IAM for secure configuration using Lambda.",
            "Deploy via ZIP, container image, or CDK for automation using Lambda."
        ]
    },
    "Heroku": {
        "subset": "DevOps",
        "bullet_points": [
            "Deploy Python web apps with zero infrastructure setup using Heroku.",
            "Use Git-based deployment and buildpacks for CI/CD using Heroku.",
            "Integrate with PostgreSQL, Redis, and other addons easily using Heroku.",
            "Scale apps horizontally using dyno settings and metrics using Heroku.",
            "Monitor logs and performance via Heroku dashboard using Heroku."
        ]
    },
    "Render": {
        "subset": "DevOps",
        "bullet_points": [
            "Deploy full-stack apps without managing infrastructure using Render.",
            "Use auto-deploy from Git repositories for CI/CD using Render.",
            "Set up custom domains, HTTPS, and autoscaling easily using Render.",
            "Monitor service logs and health metrics via dashboard using Render.",
            "Build dynamic backends, static sites, and cron jobs in one place using Render."
        ]
    },
    "Vercel": {
        "subset": "DevOps",
        "bullet_points": [
            "Deploy frontend frameworks like React, Next.js, Vue using Vercel.",
            "Enable serverless functions for backend APIs using Vercel.",
            "Preview every pull request automatically using Vercel.",
            "Connect GitHub/GitLab repos for instant deployment using Vercel.",
            "Scale apps globally with edge functions and CDN caching using Vercel."
        ]
    },
    "GitLab CI": {
        "subset": "DevOps",
        "bullet_points": [
            "Define CI/CD pipelines using `.gitlab-ci.yml` configuration using GitLab CI.",
            "Run build, test, and deploy stages in GitLab runners using GitLab CI.",
            "Automate Docker builds and deployments with GitLab CI.",
            "Use GitLab CI for canary, rollback, and multi-env deployment using GitLab CI.",
            "Visualize pipeline stages and job logs in GitLab UI using GitLab CI."
        ]
    },
    "Jenkins": {
        "subset": "DevOps",
        "bullet_points": [
            "Automate continuous integration pipelines for any project using Jenkins.",
            "Configure jobs using declarative Jenkinsfiles or UI using Jenkins.",
            "Support Docker, Kubernetes, and AWS integrations using Jenkins plugins using Jenkins.",
            "Trigger builds on Git push, PR, or scheduled events using Jenkins.",
            "Visualize job status, logs, and history in Blue Ocean UI using Jenkins."
        ]
    },
    "Gunicorn": {
        "subset": "FastAPI",
        "bullet_points": [
            "Serve WSGI applications in production with Python using Gunicorn.",
            "Use Gunicorn behind Nginx for scalable deployment using Gunicorn.",
            "Run multiple worker processes for concurrency using Gunicorn.",
            "Configure timeout, workers, and bind settings easily using Gunicorn.",
            "Deploy Flask or Django apps reliably using Gunicorn."
        ]
    },
    "Uvicorn": {
        "subset": "FastAPI",
        "bullet_points": [
            "Serve ASGI apps (FastAPI, Starlette) with high performance using Uvicorn.",
            "Enable HTTP/2 and WebSocket support natively using Uvicorn.",
            "Run in production with Gunicorn + Uvicorn workers using Uvicorn.",
            "Support hot reload for local development using Uvicorn.",
            "Deploy async APIs with low latency and memory usage using Uvicorn."
        ]
    },
    "Nginx": {
        "subset": "DevOps",
        "bullet_points": [
            "Use Nginx as a reverse proxy for backend APIs using Nginx.",
            "Serve static content and cache responses efficiently using Nginx.",
            "Configure SSL, rate-limiting, and load balancing using Nginx.",
            "Proxy traffic to app servers like Uvicorn or Gunicorn using Nginx.",
            "Enable health checks and failover routing in production using Nginx."
        ]
    },
    "Apache": {
        "subset": "DevOps",
        "bullet_points": [
            "Serve web apps and static sites using Apache HTTP Server using Apache.",
            "Use Apache as a reverse proxy or load balancer for backend services using Apache.",
            "Configure virtual hosts, SSL certificates, and rewrite rules using Apache.",
            "Support PHP, CGI, and custom modules in legacy stacks using Apache.",
            "Optimize web traffic with caching and compression using Apache."
        ]
    },
    "FastAPI throttle": {
        "subset": "FastAPI",
        "bullet_points": [
            "Implement rate limiting using FastAPI throttle libraries using FastAPI throttle.",
            "Throttle requests per IP or token to prevent abuse using FastAPI throttle.",
            "Log throttled requests for auditing and alerts using FastAPI throttle.",
            "Support Redis as a backend for distributed rate limiting using FastAPI throttle.",
            "Protect API endpoints from spamming or brute-force using FastAPI throttle."
        ]
    },
    "Redis": {
        "subset": "Redis",
        "bullet_points": [
            "Use Redis for fast in-memory caching in Python apps using Redis backend tools.",
            "Store access tokens, rate limits, and session data using Redis backend tools.",
            "Implement distributed locks for task coordination using Redis backend tools.",
            "Publish and subscribe to real-time events in microservices using Redis backend tools.",
            "Monitor Redis performance using CLI tools or dashboards using Redis backend tools."
        ]
    },
    "Redis backend tools": {
        "subset": "Redis",
        "bullet_points": [
            "Use Redis for fast in-memory caching in Python apps using Redis backend tools.",
            "Store access tokens, rate limits, and session data using Redis backend tools.",
            "Implement distributed locks for task coordination using Redis backend tools.",
            "Publish and subscribe to real-time events in microservices using Redis backend tools.",
            "Monitor Redis performance using CLI tools or dashboards using Redis backend tools."
        ]
    },
    # list top technologies used by devops
    "CircleCI": {
        "subset": "DevOps",
        "bullet_points": [
            "Run CI/CD workflows in containers or VMs using CircleCI.",
            "Define and manage build pipelines in `config.yml` using CircleCI.",
            "Use caching and parallel jobs to speed up builds using CircleCI.",
            "Connect GitHub or Bitbucket for automatic pipeline triggers using CircleCI.",
            "Monitor builds and test results from an interactive UI using CircleCI."
        ]
    },
     "Docker": {
        "subset": "Docker",
        "bullet_points": [
            "Containerize apps into lightweight, portable environments using Docker.",
            "Write and manage reproducible builds with Dockerfiles using Docker.",
            "Run, stop, and inspect services locally using Docker CLI using Docker.",
            "Push and pull container images from Docker Hub or ECR using Docker.",
            "Use Docker Compose to orchestrate multi-container apps using Docker.",
            "Debug application logs and container states using Docker.",
            "Integrate Docker into CI/CD pipelines for faster deployments using Docker.",
            "Simplify developer onboarding with prebuilt dev environments using Docker.",
            "Ensure consistent builds across machines and clouds using Docker."
        ]
    },
    "Docker Compose": {
        "subset": "Docker",
        "bullet_points": [
            "Define multi-container applications using YAML syntax using Docker Compose.",
            "Start services with a single command for local development using Docker Compose.",
            "Manage service dependencies (e.g., web + db containers) using Docker Compose.",
            "Override configuration for dev/test/prod environments using Docker Compose.",
            "Use volumes and networks for inter-container communication using Docker Compose.",
            "Run isolated test environments quickly using Docker Compose.",
            "Build, up, down, and restart containers easily using Docker Compose.",
            "Debug local development environments efficiently using Docker Compose.",
            "Replicate production-like setups on any machine using Docker Compose.",
            "Integrate Docker Compose with CI/CD tools for fast deployment testing using Docker Compose."
        ]
    },
    "Kubernetes": {
        "subset": "DevOps",
        "bullet_points": [
        "Deploy, scale, and manage containerized applications using Kubernetes.",
        "Use kubectl to interact with clusters and resources using Kubernetes.",
        "Implement config maps, secrets, and volumes for configuration using Kubernetes.",
        "Configure autoscaling, load balancing, and rolling updates using Kubernetes.",
        "Monitor pods and nodes using built-in metrics or Prometheus using Kubernetes."
        ]
    },
    "Helm": {
        "subset": "DevOps",
        "bullet_points": [
        "Package Kubernetes resources into reusable Helm charts using Helm.",
        "Install, upgrade, and rollback applications on K8s clusters using Helm.",
        "Templatize deployments with dynamic values using Helm.",
        "Store charts in Helm repositories using Helm.",
        "Manage versioned releases for environments using Helm."
        ]
    },
    "AWS": {
        "subset": "AWS",
        "bullet_points": [
        "Provision infrastructure with EC2, S3, Lambda, and RDS using AWS.",
        "Configure IAM roles, policies, and service permissions using AWS.",
        "Monitor with CloudWatch and secure using KMS using AWS."
        ]
    },
    "cloud": {
        "subset": "AWS",
        "bullet_points": [
        "Use CloudFormation, ECS, and EKS for application deployment using cloud."
        ]
    },
    "Azure": {
        "subset": "Azure",
        "bullet_points": [
            "Deploy key apps with Azure Functions, App Services, or VMs.",
            "Build key CI/CD pipelines using Azure DevOps and Boards.",
            "Secure key data with Key Vault and role-based access.",
            "Monitor key resources with Azure Monitor and Log Analytics.",
            "Automate key infra using ARM or Bicep templates in Azure."
        ]
    },
    "GCP": {
        "subset": "GCP",
        "bullet_points": [
            "Deploy key workloads using GKE, Cloud Run, or App Engine.",
            "Run key CI/CD flows with Cloud Build and Artifact Registry.",
            "Manage key IAM roles and secrets securely in GCP apps.",
            "Track key metrics via Stackdriver Monitoring in GCP.",
            "Automate key infra with Deployment Manager or Terraform."
        ]
    },
    "Terraform": {
        "subset": "DevOps",
        "bullet_points": [
            "Provision key cloud infra as code across providers in TF.",
            "Write key HCL modules for reusable infra automation code.",
            "Track key changes via `terraform plan` and `apply` flows.",
            "Use key workspaces for prod/dev/test separation in Terraform.",
            "Integrate key Terraform steps in CI/CD deployment flows."
        ]
    },
    "CloudFormation": {
        "subset": "AWS",
        "bullet_points": [
            "Define key AWS stacks using YAML/JSON templates in CFN.",
            "Manage key infra lifecycle with stacks and change sets.",
            "Use key nested stacks for modular infra provisioning.",
            "Detect key drift and track stack events in CloudFormation.",
            "Automate key provisioning via CodePipeline integration."
        ]
    },
    "Bash": {
        "subset": "DevOps",
        "bullet_points": [
        "Write shell scripts for automation, deployment, and system tasks using Bash.",
        "Parse logs, environment variables, and files using Bash.",
        "Chain CLI commands using pipes, loops, and conditionals using Bash.",
        "Create setup scripts for provisioning environments using Bash.",
        "Use in conjunction with cron jobs for scheduling using Bash."
        ]
    },
    "HashiCorp Vault": {
        "subset": "DevOps",
        "bullet_points": [
        "Store/manage key secrets, tokens, and certs via Vault tool.",
        "Use key dynamic secrets for DBs, APIs using Vault engines.",
        "Enforce key access policies with HCL and Vault ACLs setup.",
        "Audit key logs and rotate secrets securely using Vault CLI.",
        "Integrate key secrets with K8s, CI/CD flows using Vault."
        ]
    },
    "Secrets Manager": {
        "subset": "AWS",
        "bullet_points": [
        "Store and rotate key secrets securely via Secrets Manager.",
        "Control key access via IAM policies and Secrets Manager.",
        "Use key secrets in Lambda, ECS, RDS with AWS integration.",
        "Automate key secrets rotation logic via AWS Secrets Manager.",
        "Audit key secret usage via CloudTrail in AWS monitoring."
        ]
    },
    "Kubernetes Secrets": {
        "subset": "DevOps",
        "bullet_points": [
        "Store key values like DB creds securely in Kubernetes Secrets.",
        "Mount key secrets as env or volumes into K8s pods securely.",
        "Restrict key secret access via RBAC roles in Kubernetes.",
        "Integrate key secrets with Vault or SOPS using K8s plug-ins.",
        "Enable key KMS encryption for secrets at rest in K8s."
        ]
    },
    "SOPS": {
        "subset": "DevOps",
        "bullet_points": [
        "Encrypt key secrets using AWS/GCP KMS, age with SOPS tool.",
        "Store key secrets as encrypted YAML/ENV files via SOPS.",
        "Use key decryption automation in CI/CD via SOPS support.",
        "Integrate key secrets with GitOps like Flux and ArgoCD.",
        "Track key secret versions securely using SOPS in Git."
        ]
    },
    "Prometheus": {
        "subset": "DevOps",
        "bullet_points": [
        "Scrape key app metrics and service stats using Prometheus.",
        "Query key metrics with PromQL for custom dashboards setup.",
        "Set key alerts using Alertmanager integration with Prometheus.",
        "Monitor key VMs, K8s clusters, exporters with Prometheus.",
        "Push key metrics from short jobs using Prometheus gateway."
        ]
    },
    "Grafana": {
        "subset": "DevOps",
        "bullet_points": [
        "Create key dashboards from real-time data sources in Grafana.",
        "Visualize key metrics from Prometheus, Loki, CloudWatch etc.",
        "Set key alerts and thresholds for KPIs using Grafana tools.",
        "Manage key user access and roles via Grafana permissions.",
        "Embed key dashboards into portals or internal status pages."
        ]
    },
    "Elasticsearch": {
        "subset": "DevOps",
        "bullet_points": [
        "Index key logs, docs, and metrics for fast search in Elastic.",
        "Build key dashboards with Kibana using Elasticsearch data.",
        "Tune key queries and indexing performance in Elasticsearch.",
        "Apply key parsing and text analysis pipelines in Elastic.",
        "Use Elasticsearch for key analytics and observability apps."
        ]
    },
    "Logstash": {
        "subset": "DevOps",
        "bullet_points": [
        "Ingest and ship key logs to Elastic using Logstash config.",
        "Parse key structured/unstructured logs using filters in LS.",
        "Support key input/output sources like Beats, Kafka, files.",
        "Apply key enrichment and tagging to log data in Logstash.",
        "Build key pipelines for scalable log handling using LS."
        ]
    },
    "Kibana": {
        "subset": "DevOps",
        "bullet_points": [
        "Visualize key Elastic data using charts and dashboards.",
        "Query key logs and events with Lucene or KQL in Kibana.",
        "Track key system health and errors via Kibana insights.",
        "Manage key index patterns and saved views in Kibana.",
        "Set key alerts and share insights with teams via Kibana."
        ]
    },
    "Fluentd": {
        "subset": "DevOps",
        "bullet_points": [
        "Collect key logs from multiple sources using Fluentd core.",
        "Route key logs to Elastic, Kafka, or cloud sinks via Fluentd.",
        "Apply key filters and format conversion using Fluentd.",
        "Use Fluentd plugins for key integrations with outputs.",
        "Enable key log unification in cloud-native platforms."
        ]
    },
    "Fluent Bit": {
        "subset": "DevOps",
        "bullet_points": [
        "Use Fluent Bit for key edge log forwarding and parsing.",
        "Deploy key DaemonSets in Kubernetes using Fluent Bit.",
        "Stream key logs to ELK, Loki, and cloud tools reliably.",
        "Parse and filter key logs at source with Fluent Bit.",
        "Minimize key resource usage in embedded systems logging."
        ]
    },
    "Datadog": {
        "subset": "DevOps",
        "bullet_points": [
        "Monitor key metrics, apps, and infra in one place via Datadog.",
        "Set key dashboards and anomaly detection rules in Datadog.",
        "Collect key traces, logs, metrics in a single Datadog view.",
        "Use key integrations for AWS, GCP, Azure, Kubernetes, etc.",
        "Trigger key alerts based on thresholds or behaviors tracked."
        ]
    },
    "New Relic": {
        "subset": "DevOps",
        "bullet_points": [
        "Monitor key app performance and user metrics via New Relic.",
        "View key logs, traces, and metrics all in one New Relic UI.",
        "Instrument key apps for distributed tracing via New Relic.",
        "Define key SLOs, SLAs, and alerts using New Relic tools.",
        "Analyze key bottlenecks and slow requests in APM view."
        ]
    },
    "CloudWatch": {
        "subset": "AWS",
        "bullet_points": [
        "Collect key logs, metrics, and events from AWS services.",
        "Set key alarms for CPU, memory, or failures in CloudWatch.",
        "Build key dashboards to visualize trends in AWS metrics.",
        "Query key logs via Logs Insights for fast debugging.",
        "Automate key actions with CloudWatch + Lambda or SNS."
        ]
    },
    "Google Stackdriver": {
        "subset": "GCP",
        "bullet_points": [
        "Monitor key GCP apps and services via Stackdriver tools.",
        "Unify key logs, metrics, and traces in one Stackdriver UI.",
        "Set key alerts and integrate with GCP services via Stack.",
        "Track key uptime, errors, and latency trends visually.",
        "Link Stackdriver to BigQuery and Functions for key insights."
        ]
    },
    "Azure Monitor": {
        "subset": "Azure",
        "bullet_points": [
        "Collect key metrics and logs from Azure services easily.",
        "Create key alerts and dashboards for resource health.",
        "Query key insights using Log Analytics in Azure Monitor.",
        "Integrate key workflows with Logic Apps or Automation.",
        "Track key security, uptime, and performance trends fast."
        ]
    },
    "Selenium": {
        "subset": "Unittest",
        "bullet_points": [
        "Automate key browser testing across platforms with Selenium.",
        "Simulate key user actions for regression tests effectively.",
        "Run key test flows in headless mode in CI with Selenium.",
        "Use key locators and selectors to target UI elements.",
        "Integrate key tests with pytest, JUnit, or TestNG flows."
        ]
    },
    "pytest": {
        "subset": "Unittest",
        "bullet_points": [
        "Write key unit and integration tests using pytest in Python.",
        "Use key fixtures for setup and teardown in pytest tests.",
        "Generate key reports and test coverage stats via pytest.",
        "Mock key dependencies using `pytest-mock` plugin tool.",
        "Integrate key test flows into CI/CD pipelines with ease."
        ]
    },
    "Unit": {
        "subset": "Unittest",
        "bullet_points": [
        "Write key unit tests for Java code using JUnit methods.",
        "Use key annotations like @Test and @Before in Unit tests.",
        "Run key test cases via Maven, Gradle, or IDEs like IntelliJ.",
        "Export key reports in HTML or XML for CI/CD tools use.",
        "Combine with Selenium for key UI test automation flows."
        ]
    },
    "SonarQube": {
        "subset": "DevOps",
        "bullet_points": [
        "Analyze key bugs, smells, and flaws via static checks.",
        "Apply key quality gates to enforce code best practices.",
        "Visualize key code coverage and maintainability metrics.",
        "Integrate key pipelines from GitHub, Jenkins, or GitLab.",
        "Scan key codebases across Java, Python, JS, and more."
        ]
    },
    "Testcontainers": {
        "subset": "Unittest",
        "bullet_points": [
        "Spin up key Docker containers for isolated test runs.",
        "Run key integration tests with real DB or MQ in tests.",
        "Ensure key test reproducibility with fresh containers.",
        "Support key test stacks in Java, Node.js, or Python.",
        "Run key tests in CI/CD with live services via Docker."
        ]
    },
    "SSO": {
        "subset": "DevOps",
        "bullet_points": [
        "Enable key single sign-on via OAuth, SAML, or OpenID.",
        "Centralize key authentication across all enterprise apps.",
        "Use key IdPs like Azure AD or Okta for SSO setup.",
        "Improve key security and login experience via SSO.",
        "Audit key login history and session rules in SSO tools."
        ]
    },
    "OIDC": {
        "subset": "DevOps",
        "bullet_points": [
        "Secure key APIs using token-based auth via OIDC flows.",
        "Enable key federated identity via OpenID Connect auth.",
        "Integrate with key providers like Auth0 or Cognito APIs.",
        "Support key login for social or multi-tenant users.",
        "Handle key token refresh and revocation in OIDC setup."
        ]
    },
    "SAML": {
        "subset": "DevOps",
        "bullet_points": [
        "Enable key enterprise SSO using XML-based SAML flows.",
        "Integrate key IdPs like Okta or Azure AD via SAML.",
        "Allow key access to internal or SaaS apps via SAML.",
        "Map key user roles and attributes in SAML assertions.",
        "Audit key authentication attempts and logs in SAML."
        ]
    },
    "Open Policy Agent (OPA)": {
        "subset": "DevOps",
        "bullet_points": [
        "Define key policies for K8s, APIs, or Terraform in Rego.",
        "Enforce key rules using OPA with Gatekeeper or Envoy.",
        "Write key unit tests for validating OPA policy logic.",
        "Integrate key policies into CI/CD and runtime checks.",
        "Log key policy decisions and violations for auditing."
        ]
    },
    "Config": {
        "subset": "DevOps",
        "bullet_points": [
        "Track key config changes across AWS resources with Config.",
        "Define key rules to ensure compliance via AWS Config.",
        "Auto-remediate key violations using Lambda or SSM tools.",
        "View key resource history and drift with AWS Config.",
        "Integrate key logs with Security Hub and CloudTrail."
        ]
    },
    "Audit Logs": {
        "subset": "DevOps",
        "bullet_points": [
        "Monitor key user and system actions via Audit Logs daily.",
        "Track key auth events for access and config activity logs.",
        "Use key audit trails for compliance and threat detection.",
        "Integrate key logs with SIEM or ELK for deep analysis.",
        "Alert on key suspicious or critical events in log data."
        ]
    },
    "Git": {
        "subset": "DevOps",
        "bullet_points": [
        "Manage key code versions using branches and tags in Git.",
        "Follow key Git workflows like trunk-based or Git Flow.",
        "Resolve key merge conflicts and run peer reviews in Git.",
        "Use key Git hooks for automation, lint, and security.",
        "Raise key pull requests for collaborative dev in Git."
        ]
    },
    "GitHub": {
        "subset": "DevOps",
        "bullet_points": [
        "Host key codebases and branches using GitHub repos.",
        "Automate key builds and deploys via GitHub Actions.",
        "Track key issues, PRs, and workflows in GitHub boards.",
        "Collaborate via key forks, comments, and reviews daily.",
        "Enforce key security using branch rules and secrets scan."
        ]
    },
    "GitLab": {
        "subset": "DevOps",
        "bullet_points": [
        "Manage key source code, CI/CD, and projects in GitLab.",
        "Run key CI flows using GitLab runners and pipelines.",
        "Track key issues, milestones, and boards in GitLab.",
        "Apply key access control and SAST tools in GitLab.",
        "Integrate GitLab with key cloud and K8s platforms."
        ]
    },
    "Bitbucket": {
        "subset": "DevOps",
        "bullet_points": [
        "Host key Git repositories inside the Atlassian suite.",
        "Run key CI/CD builds using Bitbucket Pipelines tool.",
        "Enforce key code reviews using PR policies in Bitbucket.",
        "Link key tasks with Jira, Trello, and Confluence tools.",
        "Secure key branches with permission and deployment rules."
        ]
    },
    "Slack": {
        "subset": "DevOps",
        "bullet_points": [
        "Chat in key channels or DMs for real-time team updates.",
        "Receive key CI/CD and alert notifications in Slack chat.",
        "Connect key tools like GitHub, Jira, Opsgenie to Slack.",
        "Use key slash commands and bots for automation in Slack.",
        "Handle key incidents via alerts, ops bots, and war rooms."
        ]
    },
    "Microsoft Teams": {
        "subset": "DevOps",
        "bullet_points": [
        "Collaborate in key Teams channels for dev and ops work.",
        "Send key deployment and monitoring alerts to Teams.",
        "Co-author docs and tasks in key Teams wikis or boards.",
        "Connect Teams with key tools like GitHub or Azure DevOps.",
        "Use key bots, flows, and apps via Power Automate flows."
        ]
    },
    "JIRA": {
        "subset": "Agile",
        "bullet_points": [
        "Track key work with issues, sprints, and epic views.",
        "Set up key workflows for bug fixes and release cycles.",
        "Link key branches and commits to JIRA issues easily.",
        "Visualize key team progress with Agile boards and charts.",
        "Generate key sprint reports and velocity graphs in JIRA."
        ]
    },
    "Trello": {
        "subset": "Agile",
        "bullet_points": [
        "Manage key tasks using Trello boards and cards daily.",
        "Collaborate using key checklists, labels, and members.",
        "Link key tools like GitHub, Slack for DevOps workflows.",
        "Track key tasks via calendar or timeline Trello views.",
        "Automate key actions with Butler rules in Trello cards."
        ]
    },
    "Nexus": {
        "subset": "DevOps",
        "bullet_points": [
        "Host internal artifacts securely with Nexus in DevOps pipelines.",
        "Publish CI/CD build artifacts using Nexus for version control.",
        "Apply cleanup policies in Nexus to retain key recent builds.",
        "Control repository access with Nexus permissions and roles.",
        "Proxy third-party libraries with Nexus for faster access."
        ]
    },
    "JFrog Artifactory": {
        "subset": "DevOps",
        "bullet_points": [
        "Manage all types of binaries using JFrog Artifactory repos.",
        "Integrate JFrog Artifactory with Jenkins for CI pipelines.",
        "Use local and remote repositories via JFrog Artifactory.",
        "Control team access to repos in JFrog Artifactory setup.",
        "Promote and track builds across stages using Artifactory."
        ]
    },
    "Docker Hub": {
        "subset": "Docker",
        "bullet_points": [
        "Push and pull images from public or private Docker Hub.",
        "Set up GitHub-based auto-builds in Docker Hub easily.",
        "Host and share Docker images with teams on Docker Hub.",
        "Track image usage and stats directly via Docker Hub.",
        "Use Docker Hub in CI/CD pipelines for fast deployment."
        ]
    },
    "ECR": {
        "subset": "ECR",
        "bullet_points": [
        "Push Docker images securely to AWS ECR private repo.",
        "Scan container images for threats using AWS ECR.",
        "Control access using IAM roles for ECR repositories.",
        "Use ECR with ECS or Lambda deployments seamlessly.",
        "Apply lifecycle rules and tags in ECR for cleanup."
        ]
    },
    "Google GCR": {
        "subset": "GCP",
        "bullet_points": [
        "Push Docker images to Google GCR for GCP services.",
        "Enable fast deploys via regional Google GCR setup.",
        "Secure Google GCR with IAM roles and service accounts.",
        "Use Google GCR with GKE or Cloud Build for CI/CD.",
        "Track image versions and audit logs in Google GCR."
        ]
    },
    "PyPI": {
        "subset": "Python",
        "bullet_points": [
        "Publish Python packages to PyPI via pip or Poetry.",
        "Install public or private packages using PyPI repo.",
        "Use PyPI metadata for versioning and compatibility.",
        "Audit downloads and check vulnerabilities via PyPI.",
        "Manage Python dependencies efficiently via PyPI."
        ]
    },
    "npm": {
        "subset": "node",
        "bullet_points": [
        "Manage JavaScript packages easily using npm registry.",
        "Publish reusable modules using npm for JS projects.",
        "Run audits and fix security issues using npm tools.",
        "Define lifecycle scripts like test or build in npm.",
        "Use npm in CI pipelines for auto version publishing."
        ]
    },
    "Maven Central": {
        "subset": "DevOps",
        "bullet_points": [
        "Publish Java packages using Maven Central repository.",
        "Distribute JARs globally using Maven Central access.",
        "Enforce package naming and versioning in Maven Central.",
        "Use Maven Central via Artifactory or Nexus proxy.",
        "Monitor license and usage stats in Maven Central."
        ]
    },
    "environment": {
        "subset": "DevOps",
        "bullet_points": [
        "Debug local and remote build issues using environment tools.",
        "Switch profiles and variables across environment stages.",
        "Use `.env` or secrets managers for each environment config.",
        "Diagnose failures using logs in environment specific layers.",
        "Replicate bugs across staging and prod environment setups."
        ]
    },
    "data mining": {
        "subset": "Data",
        "bullet_points": [
        "Extract patterns from large datasets using data mining tools.",
        "Apply clustering or classification during data mining tasks.",
        "Use data mining to generate actionable business insights.",
        "Analyze unstructured logs with data mining techniques.",
        "Implement rule mining to find hidden patterns in data."
        ]
    },
    "analytics": {
        "subset": "pandas",
        "bullet_points": [
        "Perform data profiling with Pandas in analytics projects.",
        "Visualize trends and metrics in analytics using Pandas.",
        "Use groupby and pivot with Pandas for analytics workflows.",
        "Analyze structured datasets via Pandas in analytics tools.",
        "Drive business decisions with Pandas-based analytics."
        ]
    },
    "Data Analytics": {
        "subset": "pandas",
        "bullet_points": [
        "Use Pandas for cleaning and prep in Data Analytics tasks.",
        "Visualize insights using Pandas in Data Analytics projects.",
        "Generate business dashboards with Data Analytics tools.",
        "Analyze patterns in datasets with Data Analytics methods.",
        "Build KPIs and reports using Pandas for Data Analytics."
        ]
    },
    "data science": {
        "subset": "python",
        "bullet_points": [
        "Build ML pipelines using Python in data science projects.",
        "Apply EDA and feature selection in data science models.",
        "Train predictive models with Python for data science use.",
        "Use scikit-learn, TensorFlow in data science workflows.",
        "Solve real-world problems using Python data science tools."
        ]
    },
    "BigData": {
        "subset": "ETL",
        "bullet_points": [
        "Build scalable pipelines for BigData with Spark or Hadoop.",
        "Analyze massive datasets in BigData using PySpark ETL.",
        "Use distributed computing for BigData performance gains.",
        "Leverage parallel processing in BigData ETL workflows.",
        "Manage petabyte-scale data using BigData technologies."
        ]
    },
    "preprocessing": {
        "subset": "python",
        "bullet_points": [
        "Clean raw data with Python preprocessing techniques.",
        "Remove nulls, scale features during preprocessing steps.",
        "Apply encoding and binning in Python preprocessing.",
        "Normalize datasets for modeling in preprocessing stage.",
        "Transform messy inputs using Python preprocessing code."
        ]
    },
    "cleaning": {
        "subset": "python",
        "bullet_points": [
        "Clean noisy and corrupt data using Python cleaning tools.",
        "Use Pandas for handling missing data during cleaning.",
        "Standardize data types and formats during cleaning.",
        "Remove outliers and errors in data using Python cleaning.",
        "Ensure modeling readiness with proper data cleaning."
        ]
    },
    "transformation": {
        "subset": "python",
        "bullet_points": [
        "Apply data transformations using Python for modeling.",
        "Encode, scale, or bin data in transformation workflows.",
        "Aggregate values for insights during transformation step.",
        "Use Python to reshape and flatten data in transformation.",
        "Prepare model input with smart transformation logic."
        ]
    },
    "feature engineering": {
        "subset": "ai",
        "bullet_points": [
        "Generate features from raw data via feature engineering.",
        "Use Python for domain-based feature engineering logic.",
        "Transform timestamps or text for feature engineering use.",
        "Create useful metrics during feature engineering phase.",
        "Automate feature creation in AI pipelines efficiently."
        ]
    },
    "Classification": {
        "subset": "python",
        "bullet_points": [
        "Build classifiers using Python like logistic regression.",
        "Use decision trees or SVMs in Python classification tasks.",
        "Evaluate classifiers via F1-score, ROC in classification.",
        "Apply multi-class classification models using Python.",
        "Handle imbalanced datasets in Python classification."
        ]
    },
    "datasets": {
        "subset": "python",
        "bullet_points": [
        "Load datasets with Pandas and NumPy for analysis.",
        "Explore datasets using describe, info, and head in Python.",
        "Manipulate rows, columns, and types in Python datasets.",
        "Process structured/unstructured datasets via Python.",
        "Use caching and batching to manage large datasets."
        ]
    },
    "Kaggle datasets": {
        "subset": "python",
        "bullet_points": [
        "Download Kaggle datasets via API or GUI for projects.",
        "Preprocess Kaggle datasets using Python pipelines.",
        "Visualize patterns from Kaggle datasets with Matplotlib.",
        "Experiment with models on Kaggle datasets in Python.",
        "Benchmark ideas on Kaggle datasets for ML learning."
        ]
    },
    "Artificial Intelligence": {
        "subset": "ai",
        "bullet_points": [
        "Build AI models for NLP and vision using TensorFlow.",
        "Use PyTorch for training deep AI models efficiently.",
        "Apply AI techniques for automation and predictions.",
        "Leverage pretrained transformers in AI applications.",
        "Design AI pipelines for real-time decision systems."
        ]
    },
    "AI": {
        "subset": "ai",
        "bullet_points": [
        "Build AI models for NLP and vision using TensorFlow.",
        "Use PyTorch for training deep AI models efficiently.",
        "Apply AI techniques for automation and predictions.",
        "Leverage pretrained transformers in AI applications.",
        "Design AI pipelines for real-time decision systems.",
        "Solve planning problems using AI decision-making models.",
        ]
    },
     "Reinforcement Learning": {
        "subset": "ai",
        "bullet_points": [
        "Train agents using Reinforcement Learning in simulators.",
        "Improve robot pathing using Reinforcement Learning rewards.",
        "Design decision logic via Reinforcement Learning feedback.",
        ]
    },
     "Supervised Learning": {
        "subset": "ai",
        "bullet_points": [
        "Build intelligent systems using Supervised Learning logic.",
        "Build models using Supervised Learning on labeled data.",
        "Use Supervised Learning to classify customer behavior."
        ]
    },
     "Unsupervised Learning": {
        "subset": "ai",
        "bullet_points": [
        "Apply Unsupervised Learning to drive autonomous behavior.",
        "Apply Unsupervised Learning for pattern discovery in data.",
        "Use Unsupervised Learning to cluster user segments.",
        ]
    },
    "ML": {
        "subset": "ai",
        "bullet_points": [
        "Train ML models using Python libraries like XGBoost.",
        "Tune hyperparameters to boost ML model performance.",
        "Split and validate data for ML experiments properly.",
        "Deploy ML models using Flask or FastAPI services.",
        "Use cross-validation for robust ML predictions."
        ]
    },
    "Train": {
        "subset": "ML",
        "bullet_points": [
        "Train ML models using Python libraries like XGBoost.",
        "Perform Model Training on large datasets for predictions.",
        "Optimize Model Training with batch size tuning.",
        "Detect Underfitting with poor training and test accuracy.",
        "Use cross-validation for robust ML predictions."
        ]
    },
    "Model": {
        "subset": "ML",
        "bullet_points": [
        "Train ML models using Python libraries like XGBoost.",
        "Perform Model Training on large datasets for predictions.",
        "Optimize Model Training with batch size tuning.",
        "Detect Underfitting with poor training and test accuracy.",
        "Use cross-validation for robust ML predictions.",
        "Use Cross-validation to validate model generalization.",
        "Avoid Overfitting by using regularization in models.",
        ]
    },
    "Hyperparameter": {
        "subset": "ML",
        "bullet_points": [
        "Perform Cross-validation during hyperparameter tuning.",
        "Tune accuracy with Hyperparameter Tuning methods.",
        "Use grid search for Hyperparameter Tuning models.",
        ]
    },
    "machine learning": {
        "subset": "ai",
        "bullet_points": [
        "Train supervised models in machine learning pipelines.",
        "Apply ML in fraud, recommendation, or demand systems.",
        "Use unsupervised ML for clustering and anomalies.",
        "Integrate ML with analytics for smarter solutions.",
        "Evaluate machine learning models using precision/recall."
        ]
    },
    "Deep Learning": {
        "subset": "ML",
        "bullet_points": [
        "Automate Backpropagation in deep learning libraries."
        ]
    },
    "ML": {
        "subset": "ai",
        "bullet_points": [
        "Train supervised models in machine learning pipelines.",
        "Apply ML in fraud, recommendation, or demand systems.",
        "Use unsupervised ML for clustering and anomalies.",
        "Integrate ML with analytics for smarter solutions.",
        "Evaluate machine learning models using precision/recall."
        ]
    },
    "Neural Network": {
        "subset": "ML",
        "bullet_points": [
        "Design CNNs using Neural Network for image tasks.",
        "Train Neural Network to recognize handwritten digits."
        ]
    },
    "RNN": {
        "subset": "ML",
        "bullet_points": [
        "Use RNN models to predict next words in a sentence.",
        "Apply RNN for time series forecasting of sales."
        ]
    },
    "Tokenization": {
        "subset": "NLP",
        "bullet_points": [
        "Use Tokenization to split text into words for NLP.",
        "Apply Tokenization for BERT input preprocessing."
        ]
    },
    "NER": {
        "subset": "NLP",
        "bullet_points": [
        "Detect names and locations using NER techniques.",
        "Use NER to extract entities from resumes."
        ]
    },
    "Sentiment Analysis": {
        "subset": "NLP",
        "bullet_points": [
        "Perform Sentiment Analysis on customer reviews.",
        "Use Sentiment Analysis to flag negative comments."
        ]
    },
    "MLOps": {
        "subset": "MLOps",
        "bullet_points": [
        "Implement MLOps for automated CI/CD of ML pipeline.",
        "Use GitHub Actions for MLOps model retraining flow."
        ]
    },
    "AWS SageMaker": {
        "subset": "AWS",
        "bullet_points": [
        "Train models on GPU using AWS SageMaker notebooks.",
        "Deploy endpoints on AWS SageMaker with auto-scaling."
        ]
    },
    "TPU": {
        "subset": "AWS",
        "bullet_points": [
        "Speed up deep learning using GPU/TPU accelerators.",
        "Use TPU for fast training of large language models."
        ]
    },
    "TPU": {
        "subset": "AWS",
        "bullet_points": [
        "Speed up deep learning using GPU/TPU accelerators.",
        "Use TPU for fast training of large language models."
        ]
    },
    "data engineering": {
        "subset": "python",
        "bullet_points": [
        "Create ETL jobs in Python for data engineering tasks.",
        "Automate data loads using Airflow in data engineering.",
        "Design data lakes and tables in data engineering flow.",
        "Build data validation layers in data engineering stack.",
        "Use PySpark for parallel data engineering processing."
        ]
    },
    "hadoop": {
        "subset": "ETL",
        "bullet_points": [
        "Process batch data at scale using Hadoop MapReduce.",
        "Store files on HDFS in Hadoop-based ETL pipelines.",
        "Use Hive with Hadoop for SQL-like queries on big data.",
        "Integrate Hadoop and Spark for hybrid ETL processes.",
        "Build fault-tolerant jobs using Hadoop Yarn features."
        ]
    }
}
