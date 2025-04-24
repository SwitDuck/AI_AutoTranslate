import TranslatorFile
import PdfTextAnalizer
import asyncio

async def main():
    #text = ImageToText('A:\\translation')
    #text.PdfToImage()
    #text.PdfTextAnalize()
    translate = TranslatorFile()
    translator = translate.AsyncDocxTranslator()
    await translator.translate_docx(
        input_path="A:\\translation\\TextFromBook.docx",
        output_path="A:\\translation\\Translated_Text.docx",
        start_page=120,
        end_page=140
    )

if __name__ == "__main__":
    asyncio.run(main())