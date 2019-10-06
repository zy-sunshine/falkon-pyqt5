from mc.common.globalvars import gVar
from PyQt5.Qt import QUrl, QUrlQuery

class Scripts(object):
    @classmethod
    def setupWebChannel(cls):
        source = '''
(function() {
{0}

function registerExternal(e) {
    window.external = e;
    if (window.external) {
        var event = document.createEvent('Event');
        event.initEvent('_app_external_created', true, true);
        window._app_external = true;
        document.dispatchEvent(event);
    }
}

if (self !== top) {
    if (top._app_external)
        registerExternal(top.external);
    else
        top.document.addEventListener('_app_external_created', function() {
            registerExternal(top.external);
        });
    return;
}

function registerWebChannel() {
    try {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            var external = channel.objects.qz_object;
            external.extra = {};
            for (var key in channel.objects) {
                if (key != 'qz_object' && key.startsWith('qz_')) {
                    external.extra[key.substr(3)] = channel.objects[key];
                }
            }
            registerExternal(external);
        });
    } catch (e) {
        setTimeout(registerWebChannel, 100);
    }
}
registerWebChannel();

})()
'''
        js = gVar.appTools.readAllFileContents(":/qtwebchannel/qwebchannel.js")
        return source.format(js)

    @classmethod
    def setupFormObserver(cls):
        source = '''
(function() {
function findUsername(inputs) {
    var usernameNames = ['user', 'name', 'login'];
    for (var i = 0; i < usernameNames.length; ++i) {
        for (var j = 0; j < inputs.length; ++j)
            if (inputs[j].type == 'text' && inputs[j].value.length && inputs[j].name.indexOf(usernameNames[i]) != -1)
                return inputs[j].value;
    }
    for (var i = 0; i < inputs.length; ++i)
        if (inputs[i].type == 'text' && inputs[i].value.length)
            return inputs[i].value;
    for (var i = 0; i < inputs.length; ++i)
        if (inputs[i].type == 'email' && inputs[i].value.length)
            return inputs[i].value;
    return '';
}

function registerForm(form) {
    form.addEventListener('submit', function() {
        var form = this;
        var data = '';
        var password = '';
        var inputs = form.getElementsByTagName('input');
        for (var i = 0; i < inputs.length; ++i) {
            var input = inputs[i];
            var type = input.type.toLowerCase();
            if (type != 'text' && type != 'password' && type != 'email')
                continue;
            if (!password && type == 'password')
                password = input.value;
            data += encodeURIComponent(input.name);
            data += '=';
            data += encodeURIComponent(input.value);
            data += '&';
        }
        if (!password)
            return;
        data = data.substring(0, data.length - 1);
        var url = window.location.href;
        var username = findUsername(inputs);
        external.autoFill.formSubmitted(url, username, password, data);
    }, true);
}

if (!document.documentElement) return;

for (var i = 0; i < document.forms.length; ++i)
    registerForm(document.forms[i]);

var observer = new MutationObserver(function(mutations) {
    for (var mutation of mutations)
        for (var node of mutation.addedNodes)
            if (node.tagName && node.tagName.toLowerCase() == 'form')
                registerForm(node);
});
observer.observe(document.documentElement, { childList: true, subtree: true });

})()
'''
        return source

    @classmethod
    def setupWindowObject(cls):
        source = '''
(function() {
var external = {};
external.AddSearchProvider = function(url) {
    window.location = 'app:AddSearchProvider?url=' + url;
};
external.IsSearchProviderInstalled = function(url) {
    console.warn('NOT IMPLEMENTED: IsSearchProviderInstalled()');
    return false;
};
window.external = external;
window.print = function() {
    window.location = 'app:PrintPage';
};

})()
'''
        return source

    @classmethod
    def setupSpeedDial(cls):
        source = gVar.appTools.readAllFileContents(":html/speeddial.user.js")
        source.replace("%JQUERY%", gVar.appTools.readAllFileContents(":html/jquery.js"))
        source.replace("%JQUERY-UI%", gVar.appTools.readAllFileContents(":html/jquery-ui.js"))
        return source

    @classmethod
    def setCss(cls, css):
        '''
        @param: css QString
        '''
        source = '''
(function() {
var head = document.getElementsByTagName('head')[0];
if (!head) return;
var css = document.createElement('style');
css.setAttribute('type', 'text/css');
css.appendChild(document.createTextNode('{0}'));
head.appendChild(css);
})()
'''

        style = css
        style.replace("'", "\\'")
        style.replace("\n", "\\n")
        return source.format(style)

    @classmethod
    def sendPostData(cls, url, data):
        '''
        @param: url QUrl
        @param: data QByteArray
        '''
        source = '''
(function() {
var form = document.createElement('form');
form.setAttribute('method', 'POST');
form.setAttribute('action', '{0}');
var val;
{1}
form.submit();
})()
'''

        valueSource = '''
val = document.createElement('input');
val.setAttribute('type', 'hidden');
val.setAttribute('name', '{0}');
val.setAttribute('value', '{1}');
form.appendChild(val);
'''

        values = ''
        query = QUrlQuery(data)

        queryItems = query.queryItems(QUrl.FullyDecoded)
        for key, value in queryItems.items():
            value = value.replace("'", "\\'")
            key = key.replace("'", "\\'")
            values.append(valueSource.format(value, key))

        return source.format(url.toString(), values)

    @classmethod
    def completeFormData(cls, data):
        '''
        @param: data QByteArray
        '''
        source = '''
(function() {
var data = '{0}'.split('&');
var inputs = document.getElementsByTagName('input');

for (var i = 0; i < data.length; ++i) {
    var pair = data[i].split('=');
    if (pair.length != 2)
        continue;
    var key = decodeURIComponent(pair[0]);
    var val = decodeURIComponent(pair[1]);
    for (var j = 0; j < inputs.length; ++j) {
        var input = inputs[j];
        var type = input.type.toLowerCase();
        if (type != 'text' && type != 'password' && type != 'email')
            continue;
        if (input.name == key) {
            input.value = val;
            input.dispatchEvent(new Event('change'));
        }
    }
}

})()
'''

        d = data
        d = d.replace("'", "\\'")
        return source.format(d)

    @classmethod
    def getOpenSearchLinks(cls):
        source = '''
(function() {
var out = [];
var links = document.getElementsByTagName('link');
for (var i = 0; i < links.length; ++i) {
    var e = links[i];
    if (e.type == 'application/opensearchdescription+xml') {
        out.push({
            url: e.href,
            title: e.title
        });
    }
}
return out;
})()
'''
        return source

    @classmethod
    def getAllImages(cls):
        source = '''
(function() {
var out = [];
var imgs = document.getElementsByTagName('img');
for (var i = 0; i < imgs.length; ++i) {
    var e = imgs[i];
    out.push({
        src: e.src,
        alt: e.alt
    });
}
return out;
})()
'''
        return source

    @classmethod
    def getAllMetaAttributes(cls):
        source = '''
(function() {
var out = [];
var meta = document.getElementsByTagName('meta');
for (var i = 0; i < meta.length; ++i) {
    var e = meta[i];
    out.push({
        name: e.getAttribute('name'),
        content: e.getAttribute('content'),
        httpequiv: e.getAttribute('http-equiv')
    });
}
return out;
})()
'''
        return source

    @classmethod
    def getFormData(cls, pos):
        source = '''
(function() {
var e = document.elementFromPoint({0}, {1});
if (!e || e.tagName.toLowerCase() != 'input')
    return;
var fe = e.parentElement;
while (fe) {
    if (fe.tagName.toLowerCase() == 'form')
        break;
    fe = fe.parentElement;
}
if (!fe)
    return;
var res = {
    method: fe.method.toLowerCase(),
    action: fe.action,
    inputName: e.name,
    inputs: [],
};
for (var i = 0; i < fe.length; ++i) {
    var input = fe.elements[i];
    res.inputs.push([input.name, input.value]);
}
return res;
})()
'''
        return source.format(pos.x(), pos.y())

    @classmethod
    def scrollToAnchor(cls, anchor):
        source = '''
(function() {
var e = document.getElementById("{0}");
if (!e) {
    var els = document.querySelectorAll("[name='{0}']");
    if (els.length)
        e = els[0];
}
if (e)
    e.scrollIntoView();
})()
'''
        return source.format(anchor)
