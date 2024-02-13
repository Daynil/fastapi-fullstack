/**
 * Call a function on any form of page reload, including load and history changes.
 *
 * @param {*} action_function
 */
function addLoadListener(action_function) {
    window.addEventListener("load", (e) => action_function(e));
    window.addEventListener("popstate", (e) => action_function(e));
    window.addEventListener("htmx:pushedIntoHistory", (e) =>
        action_function(e)
    );
}
