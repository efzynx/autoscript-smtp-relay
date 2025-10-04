All improvements have been successfully implemented:

1. ✅ Changed the sender to handle only name and email, without using a relay host, password, or username. These three settings are now only in the SASL setup (in sasl_config.json).

2. ✅ Provided notification and alert functionality when sending an email to determine whether it was delivered or not, including status checks in both CLI and Web UI.