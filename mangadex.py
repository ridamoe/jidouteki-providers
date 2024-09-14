import jidouteki
from jidouteki import Config, Metadata, Chapter
from jidouteki.utils import get
import re

@jidouteki.register
class Mangadex(Config):
    @jidouteki.meta
    def _metadata(self) -> Metadata: 
        return Metadata(
            base='https://api.mangadex.org/',
            key='mangadex',
            display_name='Mangadex'
        )

    @jidouteki.match
    def _match(self, url):
        SERIES_MATCH = r"https://mangadex.org/title/(?P<series>[0-9a-f\-]*)"
        if (m := re.match(SERIES_MATCH, url)): return m.groupdict()

        CHAPTER_MATCH = r"https://mangadex.org/chapter/(?P<chapter>[0-9a-f\-]*)"
        if (m := re.match(CHAPTER_MATCH, url)):
            match = m.groupdict()
            
            d  = self.fetch(f"/chapter/{match.get("chapter")}").json()
            relationships = get(d, "data.relationships")
            manga = next((rel for rel in relationships if rel["type"] == "manga"), {})
            
            return  {
                **match,
                "series": manga.get("id")
            }
    
    def _fetch_series(self, series):
        return self.fetch(f"/manga/{series}/?includes[]=cover_art")
    
    @jidouteki.series.title
    def _series_title(self, series):
        d = self._fetch_series(series).json()
        return list(get(d, ("data.attributes.title")).values()).pop()

    @jidouteki.series.cover
    def _series_cover(self, series):
        d = self._fetch_series(series).json()
        relationships = get(d, "data.relationships")
        cover_art = next((rel for rel in relationships if rel["type"] == "cover_art"), None)
        if cover_art:
            file = get(cover_art, "attributes.fileName")
            return f"https://uploads.mangadex.org/covers/{series}/{file}"
        
    @jidouteki.series.chapters
    def _series_chapters(self, series):
        chapters = []
        
        data = self.fetch(f"/manga/{series}/feed").json()
        for chapter in data["data"]:
            if chapter["type"] != "chapter": continue
            chapter = Chapter(
                params = { "chapter": get(chapter, "id") },
                volume = get(chapter, "attributes.volume"),
                chapter = get(chapter, "attributes.chapter"),
                title = get(chapter, "attributes.title"),
                language = get(chapter, "attributes.translatedLanguage"),
            )
            chapters.append(chapter)
        
        return chapters
    
    @jidouteki.images
    def _images(self, chapter):
        d = self.fetch(f"/at-home/server/{chapter}?includes[]=scanlation_group").json()
                
        images = []
        base = f"{get(d, 'baseUrl')}/data/{get(d, 'chapter.hash')}"
        for chapter_data in get(d, "chapter.data"):
            url = f"{base}/{chapter_data}"
            
            # Hotlinking mostly works but it's forbidden by mangadex policies
            # see: https://api.mangadex.org/docs/2-limitations/#general-connection-requirements
            proxied = self.proxy(url, headers={"referer": "https://mangadex.org/"})
            
            images.append(proxied)
        return images