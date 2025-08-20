console.log("Hello Marion!!");
console.log("window:", window);
const currentUrl = window.location.pathname;
console.log("Current URL:", currentUrl);

// Check if the URL does not end with .html
if (!currentUrl.endsWith('.html') && currentUrl !== '/') {
    // Redirect to the same path with .html appended
    window.location.href = currentUrl + '.html';
}
