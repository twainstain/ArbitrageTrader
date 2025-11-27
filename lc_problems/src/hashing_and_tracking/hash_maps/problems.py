def is_isomorphic(string1, string2):
    if len(string1) != len(string2):
        return False
    string1_dict = {}
    string2_dict = {}
    for index in range(len(string1)):
        char_1 = string1[index]
        char_2 = string2[index]
        if (string1_dict.get(char_1) and string1_dict[char_1] != char_2) or (
                string2_dict.get(char_2) and string2_dict[char_2] != char_1):
            return False

        if not string1_dict.get(char_1):
            string1_dict[char_1] = char_2
            string2_dict[char_2] = char_1

    return True


class RequestLogger:
    def __init__(self, time_limit):
        self.timestamp_dict = {}
        self.time_limit = time_limit
        pass

    # This function decides whether the message request should be accepted or rejected
    def message_request_decision(self, timestamp, request):
        # print(f"timestamp = {timestamp}, request = {request}, time_limit = {self.time_limit}")
        message = request.lower()
        # value = self.timestamp_dict.get(message,  None)
        # if value is None:
        if not message in self.timestamp_dict:
            self.timestamp_dict[message] = timestamp
            # print(f"Adding new : timestamp = {timestamp}, request = {message}, time_limit = {self.time_limit}")
            return True
        last_time = self.timestamp_dict.get(message)
        # print(f"Existing : timestamp = {timestamp}, last_time = {last_time}, request = {message}, time_limit = {self.time_limit}")
        if timestamp - last_time >= self.time_limit:
            self.timestamp_dict[message] = timestamp
            return True

        return False