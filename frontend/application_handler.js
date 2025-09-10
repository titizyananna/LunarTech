
const WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxG9BKNeOd1LU8YUfeJr4DcizXs84K3gAteM-xgR5FdYxH8Zxq2e7OLvnC12PnZ9Cg0qw/exec"; 
const PAYMENT_AMOUNT = 1500;

function onFormSubmit(e) {
  try {
    const values = e.values;
    const sheet = SpreadsheetApp.getActiveSheet();
    const row = sheet.getLastRow(); 

    const EMAIL_COL = 1; 
    const FULL_NAME_COL = 2;
    const COUNTRY_COL = 3;
    const PHONE_COL = 4;
    const REASON_COL = 5;

    const email = values[EMAIL_COL];
    const fullName = values[FULL_NAME_COL];

    if (!email) return;

    addVerificationColumns();

    const verificationToken = Utilities.getUuid();

    sheet.getRange(row, 7).setValue(verificationToken); // G: Verification Token
    sheet.getRange(row, 8).setValue("PENDING");         // H: Verification Status
    sheet.getRange(row, 9).setValue(new Date());        // I: Verification Email Sent
    sheet.getRange(row, 11).setValue("New");            // K: Stage

    sendVerificationEmail(email, fullName, verificationToken, row);
  } catch (err) {
    console.error("onFormSubmit error:", err);
  }
}


function addVerificationColumns() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const columns = [
    "Verification Token", "Verification Status", "Verification Email Sent",
    "Email Verified At", "Stage", "Payment ID", "Scheduled Time"
  ];

  columns.forEach((name, i) => {
    if (!headers.includes(name)) sheet.getRange(1, 7 + i).setValue(name);
  });
}


function sendVerificationEmail(email, fullName, token, row) {
  const verificationUrl = `${WEB_APP_URL}?verify=${token}&row=${row}`;
  const subject = "Please Verify Your Email - LunarTech Application";
  const body = `Hello${fullName ? ", " + fullName : ""}!\n\nPlease verify your email by clicking below:\n${verificationUrl}\n\nThis link expires in 24h.`;

  MailApp.sendEmail({ to: email, subject, body });
}


function doGet(e) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const token = e.parameter.verify;
  const row = e.parameter.row;
  const action = e.parameter.action;
  const email = (e.parameter.email || "").toString().trim().toLowerCase();
  const amount = e.parameter.amount;
  const datetime = e.parameter.datetime;

  if (action === "payment" && email) return handlePaymentRequest(email);
  if (action === "schedule" && email) return showSchedulingForm(email);
  if (action === "confirm_schedule" && email && datetime) return confirmScheduling(email, datetime);

  if (action === "confirm_payment" && email) {
  return confirmPayment(email);
}

  if (token && row) {
    const storedToken = sheet.getRange(row, 7).getValue();
    const status = sheet.getRange(row, 8).getValue();
    if (storedToken === token && status === "PENDING") {
      sheet.getRange(row, 8).setValue("VERIFIED");
      sheet.getRange(row, 10).setValue(new Date());
      sheet.getRange(row, 11).setValue("Ready");

      const userData = sheet.getRange(row, 1, 1, 6).getValues()[0];
      sendReadyStageConfirmation(userData[1], userData[2]);

      return HtmlService.createHtmlOutput("<h2>Email Verified!</h2>");
    }
  }

  return HtmlService.createHtmlOutput("<h2>Invalid request</h2>");
}

function sendReadyStageConfirmation(email, fullName) {
  const paymentUrl = `${WEB_APP_URL}?action=payment&email=${encodeURIComponent(email)}`;
  const subject = "Ready for Payment - LunarTech Bootcamp";
  const body = `Hello${fullName ? ", " + fullName : ""}!\n\nYour email is verified. Complete your payment: ${paymentUrl}`;
  MailApp.sendEmail({ to: email, subject, body });
}


function handlePaymentRequest(email) {
  return HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Mock Payment</title>
      <style>
        body{font-family:sans-serif;background:linear-gradient(to right,#6a11cb,#2575fc);display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
        .container{background:#fff;color:#333;padding:40px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.2);max-width:500px;text-align:center;}
        h2{color:#2575fc;margin-bottom:20px;}
        .amount{font-size:24px;font-weight:bold;margin-bottom:30px;color:#6a11cb;}
        .pay-btn{background:#6a11cb;color:#fff;padding:15px 30px;font-size:18px;border:none;border-radius:8px;cursor:pointer;}
        .pay-btn:hover{background:#4b0fa5;}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Complete Your Payment</h2>
        <div class="amount">$${PAYMENT_AMOUNT}</div>
        <form method="GET" action="${WEB_APP_URL}">
          <input type="hidden" name="action" value="confirm_payment">
          <input type="hidden" name="email" value="${email}">
          <button type="submit" class="pay-btn">Pay Now</button>
        </form>
      </div>
    </body>
    </html>
  `);
}


function confirmPayment(email) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if ((data[i][1] || "").toLowerCase() === email && data[i][10] === "Ready") {
      const paymentId = "PAY_" + Date.now();
      sheet.getRange(i+1, 11).setValue("Paid");
      sheet.getRange(i+1, 12).setValue(paymentId);
      sendPaymentConfirmation(email, data[i][2], paymentId);
      return HtmlService.createHtmlOutput("<h2>✓ Payment Successful!</h2>");
    }
  }
  return HtmlService.createHtmlOutput("<h2>Payment Failed</h2>");
}

function sendPaymentConfirmation(email, fullName, paymentId) {
  const schedulingUrl = `${WEB_APP_URL}?action=schedule&email=${encodeURIComponent(email)}`;
  const body = `Hello${fullName ? ", " + fullName : ""}!\n\nPayment confirmed.\nSchedule your onboarding call: ${schedulingUrl}`;
  MailApp.sendEmail({ to: email, subject: "Payment Confirmed", body });
}


function showSchedulingForm(email) {
  return HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Schedule Your Call</title>
      <style>
        body{font-family:sans-serif;background:#f4f6f8;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
        .container{background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.1);max-width:500px;width:100%;text-align:center;}
        h2{color:#333;margin-bottom:20px;}
        input[type=datetime-local]{width:100%;padding:12px;margin-bottom:20px;border-radius:6px;border:1px solid #ccc;}
        .submit-btn{width:100%;padding:15px;background:#4CAF50;color:#fff;border:none;border-radius:6px;font-size:16px;cursor:pointer;}
        .submit-btn:hover{background:#45a049;}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Schedule Your Onboarding Call</h2>
        <form action="${WEB_APP_URL}" method="GET">
          <input type="hidden" name="action" value="confirm_schedule">
          <input type="hidden" name="email" value="${email}">
          <input type="datetime-local" name="datetime" required min="${new Date(Date.now()+24*60*60*1000).toISOString().slice(0,16)}">
          <button type="submit" class="submit-btn">Schedule</button>
        </form>
      </div>
    </body>
    </html>
  `);
}


function confirmScheduling(email, datetime) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if ((data[i][1] || "").toLowerCase() === email && data[i][10] === "Paid") {
      sheet.getRange(i+1, 11).setValue("Scheduled");
      sheet.getRange(i+1, 13).setValue(datetime);
      sendSchedulingConfirmation(email, data[i][2], datetime);
      return HtmlService.createHtmlOutput("<h2>✓ Scheduled!</h2>");
    }
  }
  return HtmlService.createHtmlOutput("<h2>Scheduling Failed</h2>");
}

function sendSchedulingConfirmation(email, fullName, datetime) {
  const body = `Hello${fullName ? ", " + fullName : ""}!\n\nYour onboarding call is scheduled for ${datetime}`;
  MailApp.sendEmail({ to: email, subject: "Onboarding Scheduled", body });
}
