"""
Email & SMS message templates (Bangla + English).
"""


def otp_email_template(name, otp, purpose='TRANSFER'):
    """HTML email for OTP."""
    purpose_text = {
        'LOGIN': 'Login',
        'TRANSFER': 'Fund Transfer',
        'BILL_PAYMENT': 'Bill Payment',
        'PROFILE_UPDATE': 'Profile Update',
    }.get(purpose, 'Verification')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; 
                     border-radius: 10px; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #003366, #0066cc); 
                  color: white; padding: 30px; text-align: center; }}
        .body {{ padding: 30px; }}
        .otp-box {{ background: #f0f8ff; border: 2px dashed #0066cc; 
                   padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; }}
        .otp-code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; 
                    color: #003366; font-family: monospace; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; 
                  color: #6c757d; font-size: 12px; }}
        .warning {{ color: #dc3545; font-size: 13px; margin-top: 15px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🏦 Internet Banking</h1>
          <p>One-Time Password (OTP)</p>
        </div>
        <div class="body">
          <p>প্রিয় <strong>{name}</strong>,</p>
          <p>আপনার <strong>{purpose_text}</strong> এর জন্য নিচের OTP ব্যবহার করুন:</p>

          <div class="otp-box">
            <div class="otp-code">{otp}</div>
            <p style="margin: 10px 0 0 0; color: #6c757d;">
              এই OTP ৫ মিনিটের মধ্যে ব্যবহার করুন
            </p>
          </div>

          <p style="color: #6c757d; font-size: 14px;">
            <strong>English:</strong> Your OTP for {purpose_text} is shown above. 
            Valid for 5 minutes.
          </p>

          <div class="warning">
            ⚠️ কেউ আপনার OTP জানতে চাইলে কখনো শেয়ার করবেন না। 
            ব্যাংক কখনো ফোনে OTP চায় না।
          </div>
        </div>
        <div class="footer">
          এই ইমেইল স্বয়ংক্রিয়ভাবে পাঠানো হয়েছে। রিপ্লাই করবেন না।<br>
          © 2026 Internet Banking Bangladesh. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    """


def otp_sms_template(otp, purpose='TRANSFER'):
    """SMS text for OTP (160 chars max)."""
    purpose_text = {
        'LOGIN': 'Login',
        'TRANSFER': 'Transfer',
        'BILL_PAYMENT': 'Bill',
        'PROFILE_UPDATE': 'Update',
    }.get(purpose, 'Verify')

    return (
        f"Internet Banking: Your OTP for {purpose_text} is {otp}. "
        f"Valid 5 min. Never share with anyone."
    )


def welcome_email_template(name, email):
    """Welcome email after registration."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; 
                     border-radius: 10px; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #003366, #0066cc); 
                  color: white; padding: 30px; text-align: center; }}
        .body {{ padding: 30px; }}
        .steps {{ background: #f0f8ff; padding: 20px; border-radius: 8px; }}
        .step {{ margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }}
        .cta {{ display: inline-block; background: #0066cc; color: white; 
               padding: 12px 30px; text-decoration: none; border-radius: 5px;
               margin-top: 20px; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; 
                  color: #6c757d; font-size: 12px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🏦 Welcome to Internet Banking!</h1>
        </div>
        <div class="body">
          <p>প্রিয় <strong>{name}</strong>,</p>
          <p>আপনার অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে! এখন আপনাকে KYC verify করতে হবে:</p>

          <div class="steps">
            <div class="step">📄 <strong>Step 1:</strong> KYC Submit করুন</div>
            <div class="step">🪪 <strong>Step 2:</strong> NID Front + Back + Selfie upload</div>
            <div class="step">⏱️ <strong>Step 3:</strong> 24-48 ঘন্টায় verify হবে</div>
            <div class="step">✅ <strong>Step 4:</strong> Verified হলে ব্যাংকিং শুরু</div>
          </div>

          <p style="text-align: center;">
            <a href="http://localhost:3000/kyc" class="cta">Complete KYC Now</a>
          </p>
        </div>
        <div class="footer">
          © 2026 Internet Banking Bangladesh
        </div>
      </div>
    </body>
    </html>
    """


def transaction_email_template(name, txn):
    """Transaction notification email."""
    status_color = {
        'SUCCESS': '#28a745',
        'PENDING': '#ffc107',
        'FAILED': '#dc3545',
        'HELD': '#17a2b8',
    }.get(txn.get('status'), '#6c757d')

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: white; 
                  border-radius: 10px; overflow: hidden;">
        <div style="background: {status_color}; color: white; padding: 20px; text-align: center;">
          <h2>💸 Transaction {txn.get('status', 'Update')}</h2>
        </div>
        <div style="padding: 30px;">
          <p>প্রিয় <strong>{name}</strong>,</p>
          <p>আপনার একটি লেনদেন হয়েছে:</p>
          <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background: #f8f9fa;">
              <td style="padding: 10px;"><strong>Reference</strong></td>
              <td style="padding: 10px;"><code>{txn.get('reference_no')}</code></td>
            </tr>
            <tr>
              <td style="padding: 10px;"><strong>Amount</strong></td>
              <td style="padding: 10px; font-size: 20px; color: #0066cc;">
                ৳ {txn.get('amount')}
              </td>
            </tr>
            <tr style="background: #f8f9fa;">
              <td style="padding: 10px;"><strong>Type</strong></td>
              <td style="padding: 10px;">{txn.get('transaction_type')}</td>
            </tr>
            <tr>
              <td style="padding: 10px;"><strong>Status</strong></td>
              <td style="padding: 10px;">
                <span style="background: {status_color}; color: white; 
                            padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                  {txn.get('status')}
                </span>
              </td>
            </tr>
            <tr style="background: #f8f9fa;">
              <td style="padding: 10px;"><strong>Date</strong></td>
              <td style="padding: 10px;">{txn.get('created_at', '')}</td>
            </tr>
          </table>
          <p style="color: #6c757d; font-size: 13px;">
            কোনো সমস্যা হলে সাথে সাথে আমাদের সাথে যোগাযোগ করুন।
          </p>
        </div>
      </div>
    </body>
    </html>
    """


def transaction_sms_template(txn):
    """SMS for transaction."""
    return (
        f"IB Alert: Txn {txn.get('reference_no')} "
        f"for BDT {txn.get('amount')} is {txn.get('status')}. "
        f"Balance: BDT {txn.get('new_balance', 'N/A')}"
    )


def kyc_status_email_template(name, status, remarks=''):
    """KYC approval/rejection email."""
    if status == 'APPROVED':
        color = '#28a745'
        emoji = '✅'
        title = 'KYC Approved'
        message = 'অভিনন্দন! আপনার KYC verify হয়েছে। এখন আপনি সব ব্যাংকিং সুবিধা পাবেন।'
    else:
        color = '#dc3545'
        emoji = '❌'
        title = 'KYC Rejected'
        message = 'আপনার KYC verify করা যায়নি। নিচে কারণ দেখুন এবং আবার submit করুন।'

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background: white; 
                  border-radius: 10px; overflow: hidden;">
        <div style="background: {color}; color: white; padding: 30px; text-align: center;">
          <h1>{emoji} {title}</h1>
        </div>
        <div style="padding: 30px;">
          <p>প্রিয় <strong>{name}</strong>,</p>
          <p>{message}</p>
          {f'<p style="background: #fff3cd; padding: 15px; border-radius: 5px;"><strong>কারণ:</strong> {remarks}</p>' if remarks else ''}
          <p style="text-align: center; margin-top: 30px;">
            <a href="http://localhost:3000/kyc" 
               style="background: #0066cc; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px;">
              View KYC Status
            </a>
          </p>
        </div>
      </div>
    </body>
    </html>
    """