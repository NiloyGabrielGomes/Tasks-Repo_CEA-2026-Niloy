# NOTE: The Makefile is written for Git Bash on Windows. Run `terraform apply`
# from a shell that has `make` and `bash` on PATH, or from Linux/macOS.

# ── Shared dependency layer ──────────────────────────────────────────────────
resource "null_resource" "build_layer" {
  triggers = {
    requirements_hash = filesha256("${local.backend_root}/layer/requirements.txt")
  }

  provisioner "local-exec" {
    working_dir = local.backend_root
    command     = "bash -c 'rm -rf \"${local.layer_build}/python\" && mkdir -p \"${local.layer_build}/python\" && pip install -r layer/requirements.txt -t \"${local.layer_build}/python\" --quiet'"
  }
}

data "archive_file" "layer_zip" {
  type        = "zip"
  source_dir  = local.layer_build
  output_path = "${local.build_root}/layer.zip"

  depends_on = [null_resource.build_layer]
}

# ── Per-function builds (Makefile-driven) ────────────────────────────────────
locals {
  # Hash of every Python file under src/ — invalidates all function builds on any code change.
  src_hash = sha256(join("", [
    for f in fileset("${local.backend_root}/src", "**/*.py") :
    filesha256("${local.backend_root}/src/${f}")
  ]))

  function_build_targets = {
    ingress     = "build-InteractionFunction"
    meal        = "build-MealFunction"
    location    = "build-LocationFunction"
    override    = "build-OverrideFunction"
    headcount   = "build-HeadcountFunction"
    google_chat = "build-GoogleChatFunction"
  }
}

resource "null_resource" "build_function" {
  for_each = local.function_build_targets

  triggers = {
    src_hash = local.src_hash
    target   = each.value
  }

  provisioner "local-exec" {
    working_dir = local.backend_root
    command     = "bash -c 'rm -rf \"${local.build_root}/${each.key}\" && mkdir -p \"${local.build_root}/${each.key}\" && ARTIFACTS_DIR=\"${local.build_root}/${each.key}\" make ${each.value}'"
  }
}

data "archive_file" "function_zip" {
  for_each = local.function_build_targets

  type        = "zip"
  source_dir  = "${local.build_root}/${each.key}"
  output_path = "${local.build_root}/${each.key}.zip"

  depends_on = [null_resource.build_function]
}
