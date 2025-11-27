class RequestLogger:

    # initailization of requests hash map
    def __init__(self, time_limit):
        self.requests = {}
        self.limit = time_limit

    # function to accept and deny message requests
    def message_request_decision(self, timestamp, request):

        # checking whether the specific request exists in
        # the hash map or not if it exists, check whether its
        # time duration lies within the defined timestamp
        if request not in self.requests or timestamp - self.requests[request] >= self.limit:

            # store this new request in the hash map, and return true
            self.requests[request] = timestamp
            return True

        else:
            # the request already exists within the timestamp
            # and is identical, request should
            # be rejected, return false
            return False


# driver code
def main():
    # here we will set the time limit to 7
    new_requests = RequestLogger(7)

    times = [1, 5, 6, 7, 15]
    messages = ["good morning",
                "hello world",
                "good morning",
                "good morning",
                "hello world"]

    # loop to execute over the input message requests
    for i in range(len(messages)):
        print(i + 1, ".\t Time, Message: {",
              times[i], ", '", messages[i], "'}", sep="")
        print("\t Message request decision: ",
              new_requests.message_request_decision(
                times[i], messages[i]), sep="")
        print("-" * 100)


if __name__ == '__main__':
    main()