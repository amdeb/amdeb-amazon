[![Build Status](https://travis-ci.org/amdeb/amdeb-amazon.svg?branch=master)](https://travis-ci.org/amdeb/amdeb-amazon)
[![Coverage Status](https://img.shields.io/coveralls/amdeb/amdeb-amazon.svg)](https://coveralls.io/r/amdeb/amdeb-amazon)

Amdeb Amazon Integration
============

This is an Odoo module that integrates Odoo with Amazon 
Marketplace Web Service (MWS). It supports the following functions:

* Product Synchronization
    - Upload newly created product data
    - Upload product data update: price, quantity, images, keywords etc
    - Upload product deletion
* Order Synchronization
    - Download newly created order data
    - Download order update (order cancellation)
    - Download order return request
    - Upload order confirmation
    - Upload order shipment and tracking number
    - Upload order cancellation
    - Upload return order refund

All synchronization supports two modes: an automatic mode and a manual mode.
In automatic mode, all synchronizations (including both upload and download) 
are executed by background processes at the specific interval. In manual mode,
an Odoo user can request a synchronization at any time. It can specify 
the range of synchronization or a full data synchronization. 
Following are several manual synchronization examples:

* Upload all product data to Amazon
* Download last two month's order data
* Upload this month's shipping data

Authorized Odoo users should be able to check the synchronization logs and 
should be notified when there is any error. 