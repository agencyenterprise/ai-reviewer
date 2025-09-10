import mimetypes
import os
import argparse
from markitdown import MarkItDown


class File:
    def __init__(
        self, file_path: str, file_name: str | None = None, file_type: str | None = None
    ):
        if file_name is None:
            file_name = os.path.basename(file_path)
        if file_type is None:
            file_type = mimetypes.guess_type(file_path)[0]
        self.file_name = file_name
        self.file_path = file_path
        self.file_type = file_type  # mime type

        self._markdown = None

    def _generate_markdown(self):
        if self._markdown is not None:
            return self._markdown
        md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
        result = md.convert(self.file_path)
        self._markdown = result.markdown
        return self._markdown

    @property
    def markdown(self):
        return self._generate_markdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_path",
        nargs="?",
        type=str,
        default="/Users/omid/codes/rand-ai-reviewer/lib/data/example_public_files/RAND_CFA4214-1.pdf",
    )
    args = parser.parse_args()
    file = File(file_path=args.file_path)
    print(file.markdown)
