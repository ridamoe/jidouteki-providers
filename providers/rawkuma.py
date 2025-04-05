from jidouteki import Metadata, ProviderConfig, Chapter
import jidouteki

@jidouteki.register
class Rawkuma(ProviderConfig):
    
  @jidouteki.meta
  def meta(self):
    return Metadata(
      key = "rawkuma",
      display_name = "Rawkuma",
      base = "https://rawkuma.com/"
    )
  
  @jidouteki.match
  def match(self, url):
    patterns =  (
      r"https://rawkuma\.com/(?P<series>.*?)-chapter-(?P<chapter>.*?)(?:[/?].*|)$",
      r"https://rawkuma\.com/manga/(?P<series>.*?)(?:[/?].*|)$"
    )
    
    return jidouteki.utils.match_groups(patterns, url)

  def fetch_series(self, series):
    return self.utils.fetch(f"/manga/{series}")
   
  @jidouteki.series.chapters
  def chapters(self, series):
      d = self.fetch_series(series)
      LANG = { "manga": "ja", "manhwa": "ko", "manhua": "zh" }
      type  = d.css(".tsinfo > .imptdt:nth-child(2) > a")[0].get_text()
      lang =  LANG[type.lower()]
      
      ret = []
      for el in d.css("#chapterlist li"):
        chapter = Chapter(
          params = { "chapter": el["data-num"]},
          chapter =  el["data-num"],
          language = lang
        )
        ret.append(chapter)
      return list(reversed(ret))
  
  
  @jidouteki.series.cover
  def cover(self, series):
      d = self.fetch_series(series).css(".thumbook .thumb img")
      for el in d:
        return el["src"]


  @jidouteki.series.title
  def title(self, series):
      d = self.fetch_series(series)
      d = d.css(".ts-breadcrumb.bixbox > div > span:last-child > a > span[itemprop=name]")
      for el in d: 
        return el.get_text("text")
      return None
  
  @jidouteki.images
  def images(self, series, chapter):
      d = self.utils.fetch(f"/{series}-chapter-{chapter}")
      d = d.css("#readerarea img")
      
      ret = []
      for el in d:
         url = el["src"]
         ret.append(self.utils.proxy(url, headers={"referer": "https://rawkuma.com/"}))
      return ret
      
  # search:
  #   fetcher:
  #     params:
  #       - query
  #     type: request
  #     urls: 
  #       - /?s={query}
  #   series:
  #     selector:
  #       type: css
  #       query: .bs > .bsx a
  #       pipeline:
  #         - props: 
  #           - href
  #         - regex: https://rawkuma\.com/manga/(.*?)/