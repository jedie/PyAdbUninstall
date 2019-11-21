GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details?id=%s"
EXODUS_PRIVACY_URL = "https://reports.exodus-privacy.eu.org/en/reports/search/%s/"

COLOR_LIGHT_GREEN = "#e0ffe0"
COLOR_LIGHT_RED = "#ffe0e0"
COLOR_GREY_RED="#644747"
OUTPUT_FILE = "packages.html"

# _________________________________________________________________________________________________________
# These apps can't be deinstalled via PyAdbUninstall
#
# The list based in informations from:
#   https://forum.xda-developers.com/honor-6x/how-to/guide-list-bloat-software-emui-safe-to-t3700814
#
# Please help to complete the list.
# Create pull requests on github ;)
#
LOCKED_APPS = (
    "android.process.media",  # MtpService
    "com.android.blockednumber",  # Blocked numbers feature
    "com.android.bluetooth",  # Core of Bluetooth services
    "com.android.captiveportallogin",  # Prompts login data for WiFi Hotspots
    "com.android.certinstaller",  # Certificate installer
    "com.android.companiondevicemanager",  # Companion Device Manager
    "com.android.cts.priv.ctsshim",  # Compatibilty Test Service
    "com.android.defcontainer",  # Needed for installer by applications
    "com.android.incallui",  # In Call User Interface
    "com.android.location.fused",  # GPS, Cellular and Wi-Fi networks location data
    "com.android.nfc",  # NFC service
    "com.android.phone",  # Dialer app
    "com.android.providers.contacts",  # Part of stock contact app"
    "com.android.providers.downloads",  # Download provider
    "com.android.providers.downloads.ui",  # Download app
    "com.android.providers.media",  # Needed to access media files, and ringtones
    "com.android.providers.settings",  # Sync settings
    "com.android.providers.telephony",  # Telephony provider contains data related to phone operation
    "com.android.se",  # Security Enhanced Linux (SELinux) framework
    "com.android.settings",  # Settings app
    "com.android.settings.intelligence",  # Settings tips in Settings menu
    "com.android.sharedstoragebackup",  # Possibly USB connection menu
    "com.android.shell",  # Unix shell to communicate via ADB commands through PC
    "com.android.simappdialog",  # SIM App Dialog
    "com.android.systemui",  # System User Interface
    "com.android.storagemanger",  # Storage Manager function
    "com.android.traceur",  # Android stock developer tool
    "com.google.android.apps.turbo",  # Device Health Services
    "com.android.documentsui",
    "com.google.android.ext.services",  # Android Notification Ranking service, part of Android Services Library
    "com.google.android.gms",  # Google Play Services
    "com.google.android.gsf",  # Google Services Framework
    "com.google.android.gsf.login",  # managing Google accounts
    "com.google.android.packageinstaller",  # install, update, remove apps on device
    "com.google.android.partnersetup",
    "com.google.android.webview",  # WebView interface
)
