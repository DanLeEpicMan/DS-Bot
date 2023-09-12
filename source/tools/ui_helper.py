import discord
from discord import ui
from typing import Coroutine


def generate_embed(embed_dict: dict) -> discord.Embed:
    '''
    Creates an Embed object using the given dictionary. The dictionary has no required values, and every key is optional (may be absent or assigned to `None`).\n
    Note the following type requirements for each key. See the official Embed documentation for more info.
    ```python
    author: dict {
        'name': str,
        'url': str,
        'icon_url': str
    }
    color: int
    description: str
    fields: list[dict] [
        {
            'name': str,
            'value': str,
            'inline': bool (Defaults to False)
        }
    ]
    footer: dict {
        'text': str,
        'icon_url': str
    }
    image: str
    thumbnail: str
    timestamp: datetime
    title: str
    url: str
    ```
    '''
    # safe_keys refers to what you can pass in Embed's initializer directly, unsafe_keys refers to the attributes that may only be modified via methods.
    safe_keys = {}
    unsafe_keys = {}
    for key, value in embed_dict.items():
        match key:
            case 'author' | 'fields' | 'footer' | 'image' | 'thumbnail':
                unsafe_keys[key] = value
            case _:
                safe_keys[key] = value

    embed = discord.Embed(**safe_keys)
    for key, value in unsafe_keys.items():
        match key:
            case 'author' if isinstance(value, dict):
                embed.set_author(
                    name=value['name'],
                    url=value.get('url'),
                    icon_url=value.get('icon_url')
                )
            case 'fields' if isinstance(value, list):
                for item in value:
                    embed.add_field(
                        name=item['name'],
                        value=item['value'],
                        inline=item.get('inline', False)
                    )
            case 'footer' if isinstance(value, dict):
                embed.set_footer(
                    text=value.get('text'),
                    icon_url=value.get('icon_url')
                )
            case 'image':
                embed.set_image(url=value)
            case 'thumbnail':
                embed.set_thumbnail(url=value)
            case _:
                pass
                #print('Unknown Embed key given', key, 'with value', value)

    return embed

def make_fail_embed(*, title: str, msg: str, args: dict, color: int = 0xdb1a1a):
    '''
    Return an embed displaying a failure.

    Used by the slash command `send` and context menu `edit`
    '''
    return generate_embed({
        'title': title,
        'description': msg,
        'color': color,
        'fields': [
            {
                'name': key,
                'value': str(param)
            }
            for key, param in args.items() if param and isinstance(param, (str, int, discord.Member))
        ]
    })
