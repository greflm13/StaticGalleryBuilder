from dataclasses import dataclass
from typing import List, Optional, Any, Dict, TypeVar, Callable, Type, cast

T = TypeVar("T")


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except AssertionError:
            pass
    assert False


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return {k: f(v) for (k, v) in x.items()}


def from_native_dict(f: Callable[[Any], T], x: Any) -> Dict[Any, T]:
    assert isinstance(x, dict)
    return x


@dataclass
class ImageMetadata:
    w: Optional[int]
    h: Optional[int]
    tags: Optional[List[str]]
    exifdata: Optional[Dict[str, Any]]
    xmp: Optional[Dict[str, Any]]
    src: str
    msrc: str
    name: str
    title: str
    tiff: Optional[str] = None
    raw: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> "ImageMetadata":
        assert isinstance(obj, dict)
        w = from_union([from_int, from_none], obj.get("w"))
        h = from_union([from_int, from_none], obj.get("h"))
        tags = from_union([lambda x: from_list(from_str, x), from_none], obj.get("tags"))
        exifdata = from_union([lambda x: from_native_dict(dict, x), from_none], obj.get("exifdata"))
        xmp = from_union([lambda x: from_native_dict(dict, x), from_none], obj.get("xmp"))
        src = from_str(obj.get("src"))
        msrc = from_str(obj.get("msrc"))
        name = from_str(obj.get("name"))
        title = from_str(obj.get("title"))
        tiff = from_union([from_str, from_none], obj.get("tiff"))
        raw = from_union([from_str, from_none], obj.get("raw"))
        return ImageMetadata(w, h, tags, exifdata, xmp, src, msrc, name, title, tiff, raw)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.w is not None:
            result["w"] = from_union([from_int, from_none], self.w)
        if self.h is not None:
            result["h"] = from_union([from_int, from_none], self.h)
        if self.tags is not None:
            result["tags"] = from_union([lambda x: from_list(from_str, x), from_none], self.tags)
        result["src"] = from_str(self.src)
        result["msrc"] = from_str(self.msrc)
        result["name"] = from_str(self.name)
        result["title"] = from_str(self.title)
        if self.tiff is not None:
            result["tiff"] = from_union([from_str, from_none], self.tiff)
        if self.raw is not None:
            result["raw"] = from_union([from_str, from_none], self.raw)
        if self.exifdata is not None:
            result["exifdata"] = from_union([lambda x: from_native_dict(dict, x), from_none], self.exifdata)
        if self.xmp is not None:
            result["xmp"] = from_union([lambda x: from_native_dict(dict, x), from_none], self.xmp)
        return result


@dataclass
class SubfolderMetadata:
    url: str
    name: str
    metadata: Optional[str] = None
    thumb: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> "SubfolderMetadata":
        assert isinstance(obj, dict)
        url = from_str(obj.get("url"))
        name = from_str(obj.get("name"))
        metadata = from_union([from_none, from_str], obj.get("metadata"))
        thumb = from_union([from_none, from_str], obj.get("thumb"))
        return SubfolderMetadata(url, name, metadata, thumb)

    def to_dict(self) -> dict:
        result: dict = {}
        result["url"] = from_str(self.url)
        result["name"] = from_str(self.name)
        result["metadata"] = from_union([from_none, from_str], self.metadata)
        result["thumb"] = from_union([from_none, from_str], self.thumb)
        return result


@dataclass
class Metadata:
    images: Dict[str, ImageMetadata]
    subfolders: Optional[List[SubfolderMetadata]] = None

    @staticmethod
    def from_dict(obj: Any) -> "Metadata":
        assert isinstance(obj, dict)
        images = from_dict(ImageMetadata.from_dict, obj.get("images"))
        subfolders = from_union([lambda x: from_list(SubfolderMetadata.from_dict, x), from_none], obj.get("subfolders"))
        return Metadata(images, subfolders)

    def to_dict(self) -> dict:
        result: dict = {}
        result["images"] = from_dict(lambda x: to_class(ImageMetadata, x), self.images)
        if self.subfolders is not None:
            result["subfolders"] = from_union([lambda x: from_list(lambda x: to_class(SubfolderMetadata, x), x), from_none], self.subfolders)
        return result

    def sort(self, reverse=False) -> "Metadata":
        self.images = {key: self.images[key] for key in sorted(self.images, reverse=reverse)}
        return self


def top_level_from_dict(s: Any) -> Metadata:
    return Metadata.from_dict(s)


def top_level_to_dict(x: Metadata) -> Any:
    return to_class(Metadata, x)
