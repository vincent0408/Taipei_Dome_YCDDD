# Taipei_Dome_YCDDD

A Tixcraft ticket bot with multi-threading capabilities to handle activities featuring multiple events. Some activities can include up to 60 different events on a single activity page, causing loop iteration time to be a bottleneck. This bot uses multi-threading and implements priority selection to efficiently choose available events from a large event list, given a set of user preferences.

Captcha solving was implemented using ddddocr and OpenCV to achieve a higher success rate. The speed of the bot significantly increases the probability of securing a ticket.