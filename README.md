
# vkontakte-downloader

Download Photo and Video from Wall of specific User or Community on https://vk.com

## Setup

- Clone the project

```bash
git clone https://github.com/0toshigami/vkontakte-downloader.git
```

- Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all the requirements

```bash
pip install -r requirements.txt
```

- Edit email and password in .env
It is recommended to use phone number

```
EMAIL=your_email_or_phone_number
PASS=your_password
```

## Usage

Run the follow command to start the script

```bash
py vk.py <domain> <offset> <count>
```

> domain: User or community short address ( vk.com/user01 )
>
> offset: Offset needed to return a specific subset of posts (positive number)
>
> count: Number of posts to return (positive number) (maximum 100)

For example, run `py vk.py user01 0 20` will start to get all photo or video from wall of **user01**, starting from post 0 to 19

## Bug

Tell me