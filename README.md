# TeleMediaBot

TeleMediaBot (Telegram Media and Product Automation Bot) automates media processing and product creation from messages in a specified Telegram channel.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Introduction

TeleMediaBot is designed to automate the process of handling incoming messages in a Telegram channel, downloading media, and creating products based on message content.

## Features

- Automatic media file download and processing
- Product creation from message content
- Error handling and feedback notifications
- Integration with external alert system

## Installation

### Prerequisites

- Python 3.8+
- Telegram API credentials

### Steps

1. Clone the repository:
    ```sh
    git clone https://github.com/Great0S/TKCAS.git
    ```
2. Navigate to the project directory:
    ```sh
    cd TKCAS
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Configure your settings in `config/settings.py`.
2. Run the main script:
    ```sh
    python main.py
    ```

## Configuration

Update `config/settings.py` with your Telegram API credentials and other configuration settings:
- `phone`: Your Telegram account phone number.
- `alert_bot_token`: Token for the alert bot.
- `kids_id`: ID of the Telegram channel.
- `session_name`: Name for the session file.
- `category_id`: Default category ID for products.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the contributors and libraries that made this project possible.
