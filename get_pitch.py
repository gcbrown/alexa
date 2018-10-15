def make_response(ans, end=True):
    out = {'type':'PlainText', 'text':ans}
    resp = {'outputSpeech':out, 'shouldEndSession':end}
    return {'version':'1.0', 'response':resp}
    
    
def make_ssml(ans, end=True):
    out = {'type':'SSML', 'ssml':ans}
    resp = {'outputSpeech':out, 'shouldEndSession':end}
    return {'version':'1.0', 'response':resp}


def lambda_handler(event, context):
    if event['request']['type'] == 'LaunchRequest':
        return make_response('Welcome to Pitch Pipe. What do you want to play?', False)
        
    if event['request']['type'] == 'SessionEndedRequest':
        return make_response('Goodbye!')
    
    intent = event['request']['intent']['name']
    if intent == 'AMAZON.StopIntent' or intent == 'AMAZON.CancelIntent':
        return make_response('Goodbye!')
    
    if intent == 'AMAZON.FallbackIntent' or intent == 'AMAZON.HelpIntent':
        return make_response("Try 'ask pitch pipe to play E. flat.' What do you want me to do next?", False)
        
    if intent == 'PitchIntent':
        slot = event['request']['intent']['slots']['Pitch']
        if 'resolutions' in slot and 'values' in slot['resolutions']['resolutionsPerAuthority'][0]:
            pitch = slot['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['id']
            url = 'https://raw.githubusercontent.com/gcbrown/pitch/master/{}.mp3'.format(pitch)
            speech = "<audio src='{}'/>".format(url)
            speech = '<speak>' + speech + '</speak>'
            return make_ssml(speech)
    
    return make_response("Sorry, I couldn't tell which pitch you wanted.")
