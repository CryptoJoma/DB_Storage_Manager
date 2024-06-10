<?php
// Database configuration
$host = 'localhost';
$username = 'db_user';
$password = 'db_pass';
$dbname = $_GET["dbname"];

// Your API key (store this securely and do not hard-code in production)
$valid_api_key = 'YOUR_API_KEY';

// Check for the API key in the request headers
$headers = getallheaders();
if (!isset($headers['X-API-KEY']) || $headers['X-API-KEY'] !== $valid_api_key) {
    // If the API key is missing or invalid, send a 403 Forbidden response
    header("HTTP/1.1 403 Forbidden");
    echo "Access denied.";
    exit;
}

// Set the filename for the backup file
$backup_file = $dbname . '_' . date('Ymd_His') . '.sql';

// Command to export the database
$command = "mysqldump --user={$username} --password={$password} --host={$host} {$dbname}";

// Execute the command and capture the output
$output = [];
$return_var = null;
exec($command, $output, $return_var);

if ($return_var === 0) {
    // Convert the output array to a single string
    $sql_dump = implode("\n", $output);

    // Serve the dump file for download
    header('Content-Description: File Transfer');
    header('Content-Type: application/octet-stream');
    header('Content-Disposition: attachment; filename=' . $backup_file);
    header('Expires: 0');
    header('Cache-Control: must-revalidate');
    header('Pragma: public');
    header('Content-Length: ' . strlen($sql_dump));
    echo $sql_dump;
    exit;
} else {
    // If an error occurs, send a 404 header and display an error message
    header("HTTP/1.1 404 Not Found");
    echo "Error creating the backup file.";
    exit;
}
?>
