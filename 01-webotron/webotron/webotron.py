import boto3
import click
from botocore.exceptions import ClientError
from pathlib import Path
import mimetypes

s3 = boto3.resource('s3')
client = boto3.client('s3')

@click.group()
def cli():
    'Webotron deploys website to AWS'
    pass

@cli.command('list-buckets')
def list_buckets():
    'List all s3 buckets'
    for bucket in s3.buckets.all():
        print(bucket)

@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    'Lists objects in a bucket'
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)

@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    'Create and configure a s3 bucket'
    s3_bucket = None

    try: 
        s3_bucket = s3.create_bucket( 
            Bucket=bucket, 
            CreateBucketConfiguration={'LocationConstraint': client.meta.region_name} 
        )
    except ClientError as e: 
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou': 
            s3_bucket = s3.Bucket(bucket)
            print('You already have a bucket with this name')
        else:
            raise e

    policy = """
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::%s/*"
            }
        ]
    }
    """ % s3_bucket.name
    policy = policy.strip()

    pol = s3_bucket.Policy()
    pol.put(Policy=policy)

    ws = s3_bucket.Website()
    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }
    })

    return

def upload_file(s3_bucket, path, key):
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(path, key, ExtraArgs={'ContentType': 'text/html'})

@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    'Sync local files in PATHNAME with S3 in BUCKET'

    s3_bucket = s3.Bucket(bucket)

    root = Path(pathname).expanduser().resolve()

    def handle_directory(target):
        for p in target.iterdir():
            if p.is_dir(): handle_directory(p)
            if p.is_file(): upload_file(s3_bucket, str(p), str(p.relative_to(root)))

    handle_directory(root)

if __name__ == '__main__':
    cli()
