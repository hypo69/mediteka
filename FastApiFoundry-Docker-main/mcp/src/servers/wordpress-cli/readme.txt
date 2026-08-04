What is WP-CLI
WP-CLI (WordPress Command Line Interface) is a command-line tool for managing WordPress websites without using a browser.

It allows you to:

install and update WordPress;
manage plugins, themes, and users;
perform search-and-replace operations in the database;
automate tasks through scripts.
Official website: https://wp-cli.org

Why it’s useful
Advantages of using WP-CLI:

Automation — you can write scripts for bulk operations.
Speed — command-line work is faster than the admin panel.
Flexibility — manage WordPress even without the web interface.
Security — you can disable the admin UI and work from the terminal.
Requirements
PHP 7.4+ (8.x recommended)
WordPress 3.7+
PHP CLI must be available in PATH
Internet connection for downloading files
Check PHP:

php -v
Copy
Installing WP-CLI on Windows
1. Download wp-cli.phar
Open PowerShell and run:

curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
Copy
(You can also download it manually and place it in C:\wp-cli\.)

2. Verify that it works
php C:\wp-cli\wp-cli.phar --info
Copy
If version info appears, it’s working correctly.

3. Create wp.bat
Create a file C:\wp-cli\wp.bat with the following content:

@ECHO OFF
php "%~dp0wp-cli.phar" %*
Copy
Now you can call WP-CLI simply by typing wp.

4. Add to PATH
To make wp available globally:

setx PATH "$($env:PATH);C:\wp-cli" /M
Copy
Then restart PowerShell and check:

wp --info
Copy
If the command works — installation is complete.

Alternative: Install via Composer
composer global require wp-cli/wp-cli
Copy
Then add the path:

%USERPROFILE%\AppData\Roaming\Composer\vendor\bin
Copy
Using WP-CLI
Examples of commands:

Install WordPress:

wp core download --locale=en_US
Copy
Create wp-config.php:

wp config create --dbname=wordpress --dbuser=root --dbpass=secret
Copy
Install a site:

wp core install --url="http://localhost" --title="My Site" --admin_user=admin --admin_password=1234 --admin_email=test@example.com
Copy
Updates:

wp core update
wp plugin update --all
Copy
Users:

wp user create editor editor@example.com --role=editor --user_pass=pass123
Copy
Useful commands
wp plugin list — show installed plugins
wp theme list — list all themes
wp search-replace "http://old" "https://new" — bulk search/replace
wp db export / wp db import — backup and restore the database
wp shell — open an interactive PHP shell
Full list: https://developer.wordpress.org/cli/commands/

PowerShell Script for Automatic Installation
Save this as install-wp-cli.ps1 and run as Administrator:

$targetDir = "C:\wp-cli"
$pharUrl   = "https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"
$pharPath  = "$targetDir\wp-cli.phar"
$batPath   = "$targetDir\wp.bat"

Write-Host "Installing WP-CLI..." -ForegroundColor Cyan

if (!(Test-Path $targetDir)) {
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
}

Invoke-WebRequest -Uri $pharUrl -OutFile $pharPath

"@ECHO OFF
php ""%~dp0wp-cli.phar"" %*" | Out-File $batPath -Encoding ASCII

$envPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($envPath -notlike "*$targetDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$envPath;$targetDir", "Machine")
    Write-Host "Added $targetDir to PATH (restart terminal)" -ForegroundColor Green
}

php $pharPath --info
Copy
After running it, you can use:

wp --info
Copy
Tips
Run PowerShell as Administrator when modifying PATH.
For remote sites, use --ssh=<user>@<host>.
If SSL certificate errors occur, use --skip-ssl-check.
Always back up your database before bulk operations.
Conclusion
WP-CLI is a powerful tool for WordPress administrators and developers.
It saves time, automates routine tasks, and makes management more secure and efficient.