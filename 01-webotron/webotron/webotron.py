import boto3
import click

s3 = boto3.resource('s3')

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

if __name__ == '__main__':
    cli()
