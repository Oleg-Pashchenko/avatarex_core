import requests


host = 'http://0.0.0.0:8000'
data = {
    'message': 'Привет!'
}
response = requests.post(f'{host}/api/v1/tests', data=data)


class KnowledgeAndSearchModeOLd:
    def __init__(self, data: KnowledgeAndSearchData):
        self.data: KnowledgeAndSearchData = data
        self.errors = set()
        self.responses = []

    async def _download_files_if_not_exists(self) -> bool:
        file_links = [self.data.search_database_link, self.data.knowledge_database_link]

        for file_link in file_links:
            file_id = file_link.split("id=")[1]
            output_path = f"files/{file_id}.xlsx"
            status = False
            if not os.path.exists(output_path):
                try:
                    gdown.download(file_link, output_path, quiet=True)
                    status = True
                except:
                    pass
            if not status:
                return False
        return True

    async def _is_qualification_passed(self) -> bool:  # if > 0: get question
        fields_to_fill = self.data.fields_to_fill
        for field in fields_to_fill:
            if not field['exists']:
                return False
        return True

    async def execute(self):
        download_status = self._download_files_if_not_exists()
        if not download_status:
            self.errors.add(err.UNABLE_TO_DOWNLOAD_FILE)
            answer, status = await _perephrase(self.data.service_settings_error_message, self.data)
            if status:
                self.responses.append(Message(text=answer))
            else:
                self.responses.append(Message(text=self.data.service_settings_error_message))
                self.errors.add(err.OPENAI_REQUEST_ERROR)
            return MethodResponse(data=self.responses, all_is_ok=False, errors=self.errors)

        if self._is_message_first():
            self.is_message_first = True
            answer, status = await _perephrase(self.data.hi_message, self.data)
            if status:
                self.responses.append(Message(text=answer))
            else:
                self.responses.append(Message(text=self.data.hi_message))
                self.errors.add(err.OPENAI_REQUEST_ERROR)

        if not self._is_qualification_passed():
            return QualificationMode(data=self.data, responses=self.responses, errors=self.errors,
                                     ).execute()

        return SearchMode(data=self.data, responses=self.responses, errors=self.errors,
                          ).execute()
