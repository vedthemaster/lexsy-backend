import os
import re
import uuid
from docx import Document as DocxDocument
from fastapi import HTTPException, status

from repository.document_repository import document_repo_ins


class DocumentGeneratorService:

    def __init__(self):
        self.output_dir = "uploads/generated"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_filled_document(self, document_id: str):
        """
        Generate a new document with all placeholder values filled in

        Args:
            document_id: The ID of the document to generate

        Returns:
            Returns path to generated document file
        """
        document = await document_repo_ins.get_document_by_id(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found",
            )

        unfilled = [ph.name for ph in document.placeholders if not ph.value]
        if unfilled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not all placeholders are filled. Missing: {', '.join(unfilled)}",
            )

        try:
            doc = DocxDocument(document.path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading document: {str(e)}",
            )

        replacements_made = await self._replace_placeholders_in_doc(
            doc, document.placeholders
        )

        output_filename = f"filled_{uuid.uuid4().hex}_{document.title}"
        output_path = os.path.join(self.output_dir, output_filename)

        doc.save(output_path)

        return {
            "document_id": document_id,
            "title": document.title,
            "output_path": output_path,
            "output_filename": output_filename,
            "replacements_made": replacements_made,
        }

    async def _replace_placeholders_in_doc(
        self, doc: DocxDocument, placeholders: list
    ) -> int:
        """
        Replace placeholders in the document using regex patterns
        Returns the number of replacements made
        """
        replacements_count = 0

        for placeholder in placeholders:
            if not placeholder.value:
                continue

            regex_pattern = placeholder.regex
            replacement_value = str(placeholder.value)

            for paragraph in doc.paragraphs:
                if paragraph.text:
                    original_text = paragraph.text
                    new_text = re.sub(regex_pattern, replacement_value, original_text)

                    if new_text != original_text:
                        paragraph.clear()
                        paragraph.add_run(new_text)
                        replacements_count += 1

            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            if paragraph.text:
                                original_text = paragraph.text
                                new_text = re.sub(
                                    regex_pattern, replacement_value, original_text
                                )

                                if new_text != original_text:
                                    paragraph.clear()
                                    paragraph.add_run(new_text)
                                    replacements_count += 1

        return replacements_count


document_generator_service = DocumentGeneratorService()
