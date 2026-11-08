<?php
/**
 * Plugin Name: Kaurivo Native Commerce
 * Description: Native WooCommerce storefront entry for Kaurivo websites. No simulated cart or checkout.
 * Version: 1.0.0
 * Requires Plugins: woocommerce
 * License: GPL-2.0-or-later
 */
if (!defined('ABSPATH')) { exit; }

// Never create products, prices, payment credentials or pages on activation.
// All commercial state remains in WooCommerce's actual editable catalogue.
add_shortcode('kaurivo_kauppa', function () {
    if (!class_exists('WooCommerce') || wc_get_page_id('cart') <= 0 || wc_get_page_id('checkout') <= 0) {
        return '<p role="alert">Verkkokauppa ei ole tällä hetkellä käytettävissä.</p>';
    }
    $cart = wc_get_cart_url();
    $checkout = wc_get_checkout_url();
    $output = '<section class="kaurivo-commerce woocommerce" aria-label="Verkkokauppa">';
    $output .= '<nav aria-label="Ostaminen"><a href="' . esc_url($cart) . '">Ostoskori</a> · ';
    $output .= '<a href="' . esc_url($checkout) . '">Kassalle</a></nav>';
    $output .= do_shortcode('[shop_messages]');
    $output .= get_product_search_form(false);
    $output .= do_shortcode('[product_categories number="0" parent="0" columns="3"]');
    $output .= do_shortcode('[products paginate="true" limit="12" columns="3" orderby="menu_order" order="ASC"]');
    return $output . '</section>';
});

if (defined('WP_CLI') && WP_CLI) {
    /** Sanitized native test-order evidence; no customer data or gateway secrets. */
    WP_CLI::add_command('kaurivo commerce-order-evidence', function ($args) {
        if (wp_get_environment_type() === 'production') {
            WP_CLI::error('Use an authorized sandbox/staging order.');
        }
        if (!class_exists('WooCommerce')) { WP_CLI::error('WooCommerce is not active.'); }
        $order = wc_get_order(isset($args[0]) ? absint($args[0]) : 0);
        if (!$order) { WP_CLI::error('Order not found.'); }
        $items = array();
        foreach ($order->get_items() as $line) {
            $product = $line->get_product();
            $items[] = array('product_id' => $line->get_product_id(),
                'variation_id' => $line->get_variation_id(), 'quantity' => $line->get_quantity(),
                'line_total' => $line->get_total(),
                'stock_after' => $product ? $product->get_stock_quantity() : null);
        }
        $paid = $order->get_date_paid();
        WP_CLI::line(wp_json_encode(array('protocol' => 'kaurivo-woo-order-evidence-v1',
            'environment' => wp_get_environment_type(), 'backend_url' => home_url('/'),
            'order_id' => $order->get_id(), 'transaction_id' => $order->get_transaction_id(),
            'payment_method' => $order->get_payment_method(), 'status' => $order->get_status(),
            'paid' => $order->is_paid(), 'date_paid_utc' => $paid ? gmdate('c', $paid->getTimestamp()) : null,
            'total' => $order->get_total(), 'currency' => $order->get_currency(), 'items' => $items),
            JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    });
    /** Prepare ONLY a staging installation, preserve existing pages and content. */
    WP_CLI::add_command('kaurivo commerce-setup', function ($args, $assoc) {
        if (wp_get_environment_type() === 'production') {
            WP_CLI::error('Run setup in local/development/staging first. Production changes need a reviewed migration.');
        }
        if (!class_exists('WooCommerce')) { WP_CLI::error('Install and activate WooCommerce first.'); }
        if (empty($assoc['yes'])) { WP_CLI::error('Explicit --yes is required to create missing staging pages.'); }
        $specs = array(
            array('woocommerce_shop_page_id', 'Kauppa', 'kauppa', ''),
            array('woocommerce_cart_page_id', 'Ostoskori', 'ostoskori', '[woocommerce_cart]'),
            array('woocommerce_checkout_page_id', 'Kassa', 'kassa', '[woocommerce_checkout]'),
            array('woocommerce_myaccount_page_id', 'Oma tili', 'oma-tili', '[woocommerce_my_account]')
        );
        foreach ($specs as $spec) {
            $id = absint(get_option($spec[0]));
            if ($id && get_post($id)) { continue; } // Never overwrite an existing merchant page.
            if (get_page_by_path($spec[2])) {
                WP_CLI::error('Existing unassigned page ' . $spec[2] . ': review and assign it manually; not overwriting.');
            }
            $id = wp_insert_post(array('post_type' => 'page', 'post_status' => 'publish',
                'post_title' => $spec[1], 'post_name' => $spec[2], 'post_content' => $spec[3]), true);
            if (is_wp_error($id)) { WP_CLI::error($id->get_error_message()); }
            update_option($spec[0], $id);
        }
        WP_CLI::success('Staging pages prepared. Configure verified products, shipping/tax and a test gateway; runtime QA is still required.');
    });

    /** Read-only health inventory; does not place an order or reveal secrets. */
    WP_CLI::add_command('kaurivo commerce-status', function () {
        if (!class_exists('WooCommerce')) { WP_CLI::error('WooCommerce is not active.'); }
        $pages = array();
        foreach (array('shop', 'cart', 'checkout', 'myaccount') as $key) {
            $id = wc_get_page_id($key);
            $post = $id > 0 ? get_post($id) : null;
            $pages[$key] = array('id' => $id, 'published' => $post && $post->post_status === 'publish',
                'url' => $post ? get_permalink($id) : null);
        }
        WP_CLI::line(wp_json_encode(array('backend_url' => home_url('/'),
            'environment' => wp_get_environment_type(), 'woocommerce_version' => WC_VERSION,
            'currency' => get_woocommerce_currency(), 'pages' => $pages,
            'product_count' => count(wc_get_products(array('limit' => -1, 'return' => 'ids', 'status' => 'publish'))),
            'runtime_verified' => false), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    });
}
