import subprocess
import time

# Base path for user profiles
base_profile_path = "/tmp/selenium_profile_"

# Starting remote debugging port
starting_port = 9222

# Number of profiles to launch
num_profiles = 8

# Optional: path to Chrome binary (if needed)
# chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

for i in range(1, num_profiles + 1):
    profile_path = f"{base_profile_path}{i}"
    port = starting_port + i - 1

    subprocess.Popen([
        "open", "-na", "Google Chrome",
        "--args",
        f"--user-data-dir={profile_path}",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check"
    ])

    print(f"Launched Chrome with profile {profile_path} on port {port}")
    time.sleep(0.5)  # slight delay to avoid race conditions