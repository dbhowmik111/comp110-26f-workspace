"""Download the verified model bundle using the project environment."""

from chat110.model import (
    BUNDLE_CONFIG as BUNDLE_CONFIG,
)
from chat110.model import (
    DOCUMENT_FILES as DOCUMENT_FILES,
)
from chat110.model import (
    MODEL_FILES as MODEL_FILES,
)
from chat110.model import (
    ROOT as ROOT,
)
from chat110.model import (
    BundleError as BundleError,
)
from chat110.model import (
    ensure_model as ensure_model,
)
from chat110.model import (
    file_sha256 as file_sha256,
)
from chat110.model import (
    load_config as load_config,
)
from chat110.model import (
    main,
)

if __name__ == "__main__":
    main()
