def licenseswitch(cclicense: str) -> str:
    switch = {
        "cc-zero": """
<div class="license" xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
  <a property="dct:title" rel="cc:attributionURL" href="$webroot">$title</a> by <span property="cc:attributionName">$author</span> is marked with
  <a href="https://creativecommons.org/publicdomain/zero/1.0/" target="_blank" rel="license noopener noreferrer" style="display: inline-block"
    >CC0 1.0<img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/zero.svg"
      alt=""
  /></a>
</div>
""",
        "cc-by": """
<div class="license" xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
  <a property="dct:title" rel="cc:attributionURL" href="$webroot">$title</a> by <span property="cc:attributionName">$author</span> is licensed under
  <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="license noopener noreferrer" style="display: inline-block"
    >CC BY 4.0<img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/by.svg"
      alt=""
  /></a>
</div>
""",
        "cc-by-sa": """
<div class="license" xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
  <a property="dct:title" rel="cc:attributionURL" href="$webroot">$title</a> by <span property="cc:attributionName">$author</span> is licensed under
  <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="license noopener noreferrer" style="display: inline-block"
    >CC BY-SA 4.0<img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/by.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/sa.svg"
      alt=""
  /></a>
</div>
""",
        "cc-by-nd": """
<div class="license" xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
  <a property="dct:title" rel="cc:attributionURL" href="$webroot">$title</a> by <span property="cc:attributionName">$author</span> is licensed under
  <a href="https://creativecommons.org/licenses/by-nd/4.0/" target="_blank" rel="license noopener noreferrer" style="display: inline-block"
    >CC BY-ND 4.0<img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/by.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/nd.svg"
      alt=""
  /></a>
</div>
""",
        "cc-by-nc": """
<div class="license" xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
  <a property="dct:title" rel="cc:attributionURL" href="$webroot">$title</a> by <span property="cc:attributionName">$author</span> is licensed under
  <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="license noopener noreferrer" style="display: inline-block"
    >CC BY-NC 4.0<img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/by.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/nc.svg"
      alt=""
  /></a>
</div>
""",
        "cc-by-nc-sa": """
<div class="license" xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
  <a property="dct:title" rel="cc:attributionURL" href="$webroot">$title</a> by <span property="cc:attributionName">$author</span> is licensed under
  <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="license noopener noreferrer" style="display: inline-block"
    >CC BY-NC-SA 4.0<img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/by.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/nc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/sa.svg"
      alt=""
  /></a>
</div>
""",
        "cc-by-nc-nd": """
<div class="license" xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
  <a property="dct:title" rel="cc:attributionURL" href="$webroot">$title</a> by <span property="cc:attributionName">$author</span> is licensed under
  <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank" rel="license noopener noreferrer" style="display: inline-block"
    >CC BY-NC-ND 4.0<img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/by.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/nc.svg"
      alt="" /><img
      style="height: 22px !important; margin-left: 3px; vertical-align: text-bottom"
      src="https://mirrors.creativecommons.org/presskit/icons/nd.svg"
      alt=""
  /></a>
</div>
""",
    }

    return switch.get(cclicense, "")


def licenseurlswitch(cclicense: str) -> str:
    switch = {
        "cc-zero": "https://creativecommons.org/publicdomain/zero/1.0/",
        "cc-by": "https://creativecommons.org/licenses/by/4.0/",
        "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/",
        "cc-by-nd": "https://creativecommons.org/licenses/by-nd/4.0/",
        "cc-by-nc": "https://creativecommons.org/licenses/by-nc/4.0/",
        "cc-by-nc-sa": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "cc-by-nc-nd": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    }

    return switch.get(cclicense, "")


def licensenameswitch(cclicense: str) -> str:
    switch = {
        "cc-zero": "CC0 1.0",
        "cc-by": "CC BY 4.0",
        "cc-by-sa": "CC BY-SA 4.0",
        "cc-by-nd": "CC BY-ND 4.0",
        "cc-by-nc": "CC BY-NC 4.0",
        "cc-by-nc-sa": "CC BY-NC-SA 4.0",
        "cc-by-nc-nd": "CC BY-NC-ND 4.0",
    }

    return switch.get(cclicense, "")


def licensepicswitch(cclicense: str) -> list[str]:
    switch = {
        "cc-zero": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/zero.svg",
        ],
        "cc-by": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
        ],
        "cc-by-sa": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/sa.svg",
        ],
        "cc-by-nd": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/nd.svg",
        ],
        "cc-by-nc": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/nc.svg",
        ],
        "cc-by-nc-sa": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/nc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/sa.svg",
        ],
        "cc-by-nc-nd": [
            "https://mirrors.creativecommons.org/presskit/icons/cc.svg",
            "https://mirrors.creativecommons.org/presskit/icons/by.svg",
            "https://mirrors.creativecommons.org/presskit/icons/nd.svg",
        ],
    }

    return switch.get(cclicense, "")
