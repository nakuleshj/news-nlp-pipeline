resource "aws_s3_bucket" "bronze" {
    bucket= "raw"
}
resource "aws_s3_bucket" "silver" {
    bucket= "enriched"
}