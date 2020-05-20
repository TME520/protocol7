#! /bin/bash

echo "Starting DynamoDB, listening on port 8001..."
cd $HOME/dynamodb_local_latest/
pwd
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -port 8001
echo "...done."

exit 0
