from flask import Flask, request, jsonify
import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET", "")
PROFILE_NAME = os.getenv("PROFILE_NAME", "")

try:
    session = boto3.Session(profile_name=PROFILE_NAME)
    s3_client = session.client("s3")
    AWS_REGION = session.region_name or 'us-east-1'
    
    try:
        response = s3_client.list_buckets()
        logger.info(f"Successfully connected to S3. Found {len(response['Buckets'])} buckets.")
        
        bucket_names = [bucket['Name'] for bucket in response['Buckets']]
        
        # Check if our target bucket exists
        if S3_BUCKET in bucket_names:
            logger.info(f"Target bucket '{S3_BUCKET}' found in account")
        else:
            logger.warning(f"Target bucket '{S3_BUCKET}' NOT found in account")
            logger.warning("Please verify the bucket name and that you have access to it")
            
    except ClientError as list_error:
        logger.error(f"Failed to list buckets: {list_error}")
        raise
    
    # test to see if I can access the bucket
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
    except ClientError as bucket_error:
        error_code = bucket_error.response['Error']['Code']
        error_message = bucket_error.response['Error']['Message']
        
        logger.error(f"Error accessing bucket '{S3_BUCKET}': {error_code} - {error_message}")
        
        if error_code == '400':
            logger.error("Bad Request - This could mean:")
            logger.error("1. Invalid bucket name format")
            logger.error("2. Bucket doesn't exist")
            logger.error("3. Bucket is in a different region")
            
            # Try to get bucket location if it exists
            try:
                location_response = s3_client.get_bucket_location(Bucket=S3_BUCKET)
                actual_region = location_response['LocationConstraint'] or 'us-east-1'
                logger.info(f"Bucket '{S3_BUCKET}' is actually in region: {actual_region}")
                if actual_region != AWS_REGION:
                    logger.error(f"Region mismatch! Bucket is in '{actual_region}' but client is configured for '{AWS_REGION}'")
            except ClientError as loc_error:
                logger.error(f"Could not determine bucket location: {loc_error}")
                
        elif error_code == '404' or error_code == 'NoSuchBucket':
            logger.error(f"Bucket '{S3_BUCKET}' does not exist")
        elif error_code == 'Forbidden' or error_code == '403':
            logger.error(f"Access denied to bucket '{S3_BUCKET}' - check your permissions")
        
        raise bucket_error
        
except NoCredentialsError:
    logger.error("AWS credentials not found")
    raise
except Exception as e:
    logger.error(f"Unexpected error initializing S3 client: {e}")
    raise


@app.route("/upload", methods=["POST"])
def upload_files():
    logger.info("Received request to upload files")
    
    if not request.files:
        return jsonify({"error": "No files provided"}), 400

    uploaded_files = {}
    errors = []

    for file_key in request.files:
        file_list = request.files.getlist(file_key)
        uploaded_files[file_key] = []

        for file in file_list:
            if file.filename == '':
                errors.append(f"Empty filename in {file_key}")
                continue
                
            try:
                # Reset file pointer to beginning
                file.seek(0)
                
                s3_key = f"{file_key}/{file.filename}"
                
                # Upload with explicit content type
                s3_client.upload_fileobj(
                    file, 
                    S3_BUCKET, 
                    s3_key,
                    ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'}
                )
                
                file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
                uploaded_files[file_key].append({
                    "filename": file.filename,
                    "url": file_url,
                    "s3_key": s3_key
                })
                logger.info(f"Successfully uploaded {file.filename} to {file_url}")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                error_msg = f"Failed to upload {file.filename}: {error_code} - {error_message}"
                errors.append(error_msg)
                logger.error(error_msg)
                
            except Exception as e:
                error_msg = f"Unexpected error uploading {file.filename}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

    # Return response with both successes and errors
    response_data = {
        "message": "Upload process completed",
        "uploaded_files": uploaded_files
    }
    
    if errors:
        response_data["errors"] = errors
        status_code = 207  # Multi-Status
    else:
        response_data["message"] = "All files uploaded successfully"
        status_code = 200

    return jsonify(response_data), status_code


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify S3 connectivity"""
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        return jsonify({"status": "healthy", "s3_connection": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)