from datetime import date
from pathlib import Path

from spotify_albums import load_config, load_credentials, load_urls, write_to_markdown, load_markdown_albums, get_albums, build_dataframe, build_page

ROOT = Path(__file__).parent
load_credentials(ROOT / 'spotify_albums' / 'spotify_credentials.sh')

paths = load_config(ROOT / 'config' / 'paths.yaml')


def get_new_albums():
    urls_list = load_urls(paths["links"])
    albums = get_albums(urls_list)
    albums_listened = load_markdown_albums(paths["listened"])
    albums_not_listened = load_markdown_albums(paths["not_listened"])
    albums_not_listened = [album for album in albums_not_listened if album not in albums_listened]
    new_albums = [album for album in albums if album not in albums_listened]
    new_albums = [album for album in new_albums if album not in albums_not_listened]
    return sorted(albums_not_listened + new_albums)


if __name__ == '__main__':
    albums = get_new_albums()
    write_to_markdown(albums, paths["not_listened"])

    listened = sorted(load_markdown_albums(paths["listened"]))
    write_to_markdown(listened, paths["listened"])

    with open(paths["links"], 'w') as f:
        f.write('')

    df = build_dataframe(paths["listened"])
    df.to_csv(Path('csv') / f'albums_{date.today().strftime("%Y%m%d")}.csv', index=False)
    print(df.to_string(index=False))

    img = sorted(Path('img').glob('*.png'))[-1]
    build_page(df, img, Path('index.html'), formspree_url=paths.get('formspree_url', ''))
