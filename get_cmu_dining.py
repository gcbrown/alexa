from botocore.vendored import requests
import datetime
import pytz

global_t = datetime.datetime.now(pytz.timezone('America/New_York'))
global_t = datetime.timedelta(days=(global_t.weekday() + 1) % 7, hours=global_t.hour, minutes=global_t.minute)
week = datetime.timedelta(days=7)


def make_response(ans, end=True):
    out = {'type':'PlainText', 'text':ans}
    resp = {'outputSpeech':out, 'shouldEndSession':end}
    return {'version':'1.0', 'response':resp}


def till_change(times):
    till_opens = []
    for time in times:
        t = global_t
        s = time['start']
        s = datetime.timedelta(days=s['day'], hours=s['hour'], minutes=s['min'])
        e = time['end']
        e = datetime.timedelta(days=e['day'], hours=e['hour'], minutes=e['min'])
        if e < s:
            if t < e:
                t += week
            e += week
        if s < t < e:
            return (e - t).total_seconds() / 60
        else:
            if s < t:
                s += week
            till_opens.append((t - s).total_seconds() / 60)
    return max(till_opens)


def get_till(l):
    return sorted(((loc['name'], till_change(loc['times'])) for loc in l), key=lambda x:x[1])
    
    
def format_delta(d):
    d = abs(d)
    days = int(d / 1440)
    if days:
        return '{} day{}'.format(days, 's' if days != 1 else '')
    hours = int(d / 60)
    if hours:
        return '{} hour{}'.format(hours, 's' if hours != 1 else '')
    mins = int(d)
    return '{} minute{}'.format(mins, 's' if mins != 1 else '')
    
    
def oxford(l):
    if len(l) == 1:
        return l[0]
    if len(l) == 2:
        return l[0] + ' and ' + l[1]
    return ', '.join(l[:-1]) + ', and {}'.format(l[-1])
    
    
def get_open(l):
    o = get_till(l)
    soon_time = 60
    soon = [loc[0] for loc in o if loc[1] > 0 and loc[1] < soon_time]
    later = [loc[0] for loc in o if loc[1] > 0 and loc[1] > soon_time]
    
    ans = ''
    if soon:
        ans += 'Closing soon: ' + oxford(soon) + '. '
    if later:
        ans += 'Currently open: ' + oxford(later) + '.'
    if not ans:
        ans = "Sorry, I couldn't find anything that's open."
    return ans


def lambda_handler(event, context):
    if event['request']['type'] == 'LaunchRequest':
        return make_response('Where, or what, would you like to eat?', False)
        
    if event['request']['type'] == 'SessionEndedRequest':
        return make_response('Goodbye!')
    
    intent = event['request']['intent']['name']
    if intent == 'AMAZON.StopIntent' or intent == 'AMAZON.CancelIntent':
        return make_response('Goodbye!')
    
    if intent == 'AMAZON.FallbackIntent':
        return make_response("Bark, bark. I couldn't tell what you wanted. Try saying, 'Alexa, ask Scotty Dog if The Exchange is open.'")
        
    if intent == 'AMAZON.HelpIntent':
        return make_response("Try asking me what's open, where to get pizza, or if The Pomegranate is open. What would you like to check on?", False)
        
    l = requests.get('https://apis.scottylabs.org/dining/v1/locations').json()['locations']
    if intent == 'AllLocationsIntent':
        return make_response(get_open(l))
        
    if intent == "LocationStatusIntent":
        loc_json = event['request']['intent']['slots']['Location']['resolutions']['resolutionsPerAuthority'][0]
        if 'values' in loc_json:
            name = loc_json['values'][0]['value']['name']
        else:
            return make_response("Sorry, I couldn't tell which restaurant you wanted.")
            
        loc = next(loc for loc in l if loc['name'] == name)
        loc_open = till_change(loc['times'])
        if loc_open > 0:
            ans = name + ' is open.'
            ans += ' It will close in {}.'.format(format_delta(loc_open))
        else:
            ans = name + ' is closed.'
            ans += ' It will open in {}.'.format(format_delta(loc_open))
        return make_response(ans)
        
    if intent == 'KeywordIntent':
        loc_json = event['request']['intent']['slots']['Keyword']
        if 'values' in loc_json['resolutions']['resolutionsPerAuthority'][0]:
            keyword = loc_json['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']
        else:
            keyword = loc_json['value']
            
        l = [loc for loc in l if keyword in loc['keywords'] or keyword in loc['description']]
        return make_response(get_open(l))
        
    if intent == 'PlacesIntent':
        loc_json = event['request']['intent']['slots']['Place']
        if 'resolutions' in loc_json and 'values' in loc_json['resolutions']['resolutionsPerAuthority'][0]:
            place = loc_json['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']
        else:
            return make_response("Sorry, I couldn't tell where you wanted. Try 'Alexa, ask Scotty Dog what's open in Resnik.'")
        
        l = [loc for loc in l if place in loc['location']]
        return make_response(get_open(l))
        