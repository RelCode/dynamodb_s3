import boto3

session = boto3.Session(profile_name="product-newlexis-dev-lexisadvancedeveloper")
s3 = session.client("s3")

buckets = s3.list_buckets()
for b in buckets['Buckets']:
    print(b['Name'])