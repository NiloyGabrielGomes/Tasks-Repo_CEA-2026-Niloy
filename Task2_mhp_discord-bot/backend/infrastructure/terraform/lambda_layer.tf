resource "aws_lambda_layer_version" "shared_deps" {
  layer_name               = "${var.name_prefix}-deps"
  filename                 = data.archive_file.layer_zip.output_path
  source_code_hash         = data.archive_file.layer_zip.output_base64sha256
  compatible_runtimes      = ["python3.12"]
}
