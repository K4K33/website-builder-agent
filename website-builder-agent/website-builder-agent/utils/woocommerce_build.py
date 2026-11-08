"""Prepare a native integration, not a paid-provider call or a fake storefront.

The artifact must be installed into the SAME editable WP/WooCommerce staging
site used for previews. This function does not install software or transact.
"""
from hashlib import sha256
from pathlib import Path
import json
import zipfile
from utils.commerce_workflow import validate_commerce_plan, CASES
from utils.service_quality import service_brief


class CommerceStagingRequired(RuntimeError):
    def __init__(self, result):
        self.result = result
        super().__init__('Native commerce package prepared at ' + result['archive'] +
                         '; install/test the real editable staging backend before claiming a built store')


def prepare_woocommerce_build(research, output_dir):
    plan = validate_commerce_plan(research)
    if plan['mode'] != 'woocommerce_native':
        raise RuntimeError('build-commerce requires an inspected woocommerce_native plan')
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    plugin = Path(__file__).resolve().parents[1] / 'templates/woocommerce-native/kaurivo-commerce.php'
    content = plugin.read_bytes()
    manifest = {'protocol': 'commerce-v1', 'mode': 'woocommerce_native',
        'status': 'prepared_not_runtime_verified', 'backend_url': plan['backend_url'],
        'contract_sha256': service_brief(research)['contract_sha256'],
        'plugin_sha256': sha256(content).hexdigest(),
        'runtime_verified': False, 'client_release_ready': False,
        'required_tests': list(CASES), 'required_viewports': ['desktop', 'mobile'],
        'required_product_data': ['source product identifier', 'native product/variation mapping',
            'verified price/currency/tax class', 'stock', 'delivery', 'returns'],
        'note': 'No store, gateway, catalogue import, order or payment has been provisioned by this package.'}
    instructions = '''# Kaurivo: native commerce staging

Use this plugin inside the same WordPress/WooCommerce implementation that
will be editable and delivered to the client. A separate static mockup is not
the commerce preview. Use the company's chosen individual theme; this plugin
does not impose Kaurivo's visual template or replace the original brand.

1. Install and activate WooCommerce and this plugin on an authorized staging
   site. No activation hook creates products or changes merchant configuration.
2. Set WordPress environment to staging/local/development. Review existing
   page assignments first. Run `wp kaurivo commerce-setup --yes` to create only
   missing native pages. Existing pages and content are never overwritten.
3. Import or map the verified source catalogue. Never guess prices, variants,
   stock, delivery, tax or returns. No demo products belong in live inventory.
4. Shop uses native WooCommerce product/category/search rendering. Product
   pages and variable products use the real WooCommerce theme. Cart, checkout
   and account page content use native WooCommerce shortcodes/blocks. Preserve
   page content in the theme; do not substitute hardcoded checkout HTML.
   The assigned Shop page uses the theme's native archive, with no duplicate
   shortcode product loop in its description. [kaurivo_kauppa] is available
   for a separate art-directed landing page within that same installation.
5. Configure source-approved shipping/tax and the selected gateway in TEST
   mode. Use authorized test addresses. Do not send tests to the business or
   perform live transactions. `wp kaurivo commerce-status` is read-only status,
   not an acceptance certificate.
6. Execute every manifest test on desktop/mobile, including failures,
   cancellation, stock changes, duplicate callback and customer product edit.
   Record exact deployment/backend/build/contract and actual private evidence
   under delivery.commerce_runtime; collect it with review-material. Inspect
   the resulting order/payment references and notices. A success URL is not
   payment proof. Fixture/unit tests are not this runtime evidence.
7. Before production: actual CMS save/publish/restore, payment/shipping/order
   tests, independent visual review and client signoff must pass. This artifact
   alone is NOT a completed website or a verified commerce deployment.

Use `wp kaurivo commerce-order-evidence ORDER_ID` only for authorized staging
test orders. Save its sanitized JSON privately as transaction_capture_path;
after review-material collection, set transaction_evidence_id to the actual
commerce_backend_trace item ID. No customer details or gateway secrets are
exported. A paid native order with a transaction reference is required; the
export and captures still need independent review. No mock/fixture may stand
in for this real test-gateway evidence.
'''
    archive = root / 'kaurivo-native-commerce.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('kaurivo-native-commerce/kaurivo-commerce.php', content)
        z.writestr('kaurivo-native-commerce/README.md', instructions)
    manifest['archive_sha256'] = sha256(archive.read_bytes()).hexdigest()
    (root / 'commerce-build.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (root / 'COMMERCE_SETUP.md').write_text(instructions, encoding='utf-8')
    return {**manifest, 'archive': str(archive)}
