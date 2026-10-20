/* Legacy NeoVis pages only. A browser-visible connection is never a secret.
 * Use a dedicated read-only account in a trusted local environment.
 * Public deployments should obtain graph data from an authenticated backend.
 */
function getPesticideGraphConnection() {
    var config = window.PESTICIDE_NEO4J_CONFIG || {};
    if (!config.server_url || !config.server_user || !config.server_password) {
        return null;
    }
    return {
        server_url: config.server_url,
        server_user: config.server_user,
        server_password: config.server_password
    };
}
