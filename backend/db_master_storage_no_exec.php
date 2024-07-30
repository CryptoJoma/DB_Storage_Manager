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
if (!isset($headers['X-Api-Key']) || $headers['X-Api-Key'] !== $valid_api_key) {
    // If the API key is missing or invalid, send a 403 Forbidden response
    header("HTTP/1.1 403 Forbidden");
    die("Access denied.");
}

// Connect to the database
$mysqli = new mysqli($host, $username, $password, $dbname);

// Check connection
if ($mysqli->connect_error) {
  header("HTTP/1.1 404 Not Found");
  die("Connection failed: " . $mysqli->connect_error);
}

// Set the filename for the backup file
$backup_file = $dbname . '_' . date('Ymd_His') . '.sql';

// Function to generate SQL dump
function getTableCreateSQL($mysqli, $table) {
    $result = $mysqli->query("SHOW CREATE TABLE `$table`");
    $row = $result->fetch_array();
    return $row[1] . ";\n\n";
}

function getTableDataSQL($mysqli, $table) {
    $sql = "";
    $result = $mysqli->query("SELECT * FROM `$table`");
    while ($row = $result->fetch_assoc()) {
        $sql .= "INSERT INTO `$table` (" . implode(", ", array_keys($row)) . ") VALUES ('" . implode("', '", array_map([$mysqli, 'real_escape_string'], array_values($row))) . "');\n";
    }
    return $sql . "\n";
}

// Get list of tables
$tables = [];
$result = $mysqli->query("SHOW TABLES");
while ($row = $result->fetch_array()) {
    $tables[] = $row[0];
}

// Generate SQL dump
$sql_dump = "";
foreach ($tables as $table) {
    $sql_dump .= getTableCreateSQL($mysqli, $table);
    $sql_dump .= getTableDataSQL($mysqli, $table);
}

// Close database connection
$mysqli->close();

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
?>
