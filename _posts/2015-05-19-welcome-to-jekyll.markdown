---
layout: post
title:  "Hello World"
date:   2015-05-19 22:14:17
categories: first
---

Hello World!

{% highlight ruby %}
def hello_world():
    print "Hello World!"
{% endhighlight %}

  {% if author %}
      <span>
          <!-- Mugshot. -->
          <img src="{{ author.email | to_gravatar }}" alt="A photo of {{ author.name }}" />

          <!-- Personal Info. -->
          Written by <a href="{{ author.web }}" target="_blank">{{ author.name }}</a>
      </span>
  {% endif %}

