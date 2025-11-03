# HOW_TO_GET_AND_SET_CDDIS_COOKIE.md

This guide explains how to manually obtain your NASA Earthdata/CDDIS cookie 
and load it into your system environment for authenticated data access. 
-------------------------------------------------------------------------
🧭 STEP 1 — Manually get your Earthdata cookie
-------------------------------------------------------------------------

1. Open your web browser (Chrome, Firefox, or Edge).

2. Go to a CDDIS data URL that requires authentication, for example:
   https://cddis.nasa.gov/archive/gnss/data/daily/2025/brdc/
   It will redirect you to NASA’s Earthdata login page (urs.earthdata.nasa.gov).

3. Log in with your Earthdata credentials.

4. Once logged in, open Developer Tools:
   - Chrome / Edge:  F12 → Application tab → Storage → Cookies
   - Firefox:        F12 → Storage tab → Cookies

5. Locate the domain:
   - Usually `urs.earthdata.nasa.gov`
   - Sometimes also `cddis.nasa.gov`

6. Find the session cookie (commonly named `urs` or `session`).

7. Copy the full `name=value` of that cookie. For example:
    urs=abcdef1234567890abcdef

8. If you need multiple cookies, join them with semicolons and spaces:
      urs=abcdef1234567890abcdef; another_cookie=xyz123

9. Keep this value secret — it is equivalent to your login session token.
   Do not share or commit it to source control.

-------------------------------------------------------------------------
🖥️ STEP 2 — Load the cookie into your system environment
-------------------------------------------------------------------------

Create an environment variable called CDDIS_COOKIE and assign the cookie string.

---- Linux / macOS (bash or zsh) ----

Run this in your terminal:
  export CDDIS_COOKIE='urs=abcdef1234567890abcdef'

To make it persist for future sessions, add the same line to:
  ~/.bashrc   or   ~/.zshrc

---- Windows PowerShell ----

Run this in your PowerShell terminal:
  $env:CDDIS_COOKIE = 'urs=abcdef1234567890abcdef'

To store it permanently:
   - Open Control Panel → System → Advanced → Environment Variables
   - Add a new User or System variable:
      Name:  CDDIS_COOKIE
      Value: urs=abcdef1234567890abcdef

---- Windows CMD (temporary session) ----

  set CDDIS_COOKIE=urs=abcdef1234567890abcdef

-------------------------------------------------------------------------
🔒 NOTES
-------------------------------------------------------------------------

• Treat this cookie like a password — do not share or upload it.
• If your cookie stops working (403 errors or redirect to login),
  repeat STEP 1 to obtain a new session cookie and update the variable.
• Verify the variable is set correctly:
    Linux/macOS →  echo $CDDIS_COOKIE
    PowerShell   →  echo $env:CDDIS_COOKIE
    CMD          →  echo %CDDIS_COOKIE%

-------------------------------------------------------------------------
✅ Summary
-------------------------------------------------------------------------

- Copy the cookie value from your logged-in browser.
- Store it as an environment variable named `CDDIS_COOKIE`.
- Keep it private and refresh it periodically when expired.

# End of HOW_TO_GET_AND_SET_CDDIS_COOKIE.md
