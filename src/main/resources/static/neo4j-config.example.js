/* Copy to neo4j-config.local.js for trusted local legacy-page use only.
 * The local file is ignored by Git, but its values remain visible to browsers.
 * Never use an administrator account here. The Agent demo does not use this file.
 */
window.PESTICIDE_NEO4J_CONFIG = {
    server_url: "bolt://localhost:7687",
    server_user: "readonly_user",
    server_password: ""
};
