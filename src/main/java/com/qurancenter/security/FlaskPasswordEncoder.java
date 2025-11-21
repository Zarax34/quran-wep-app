package com.qurancenter.security;

import org.springframework.security.crypto.password.PasswordEncoder;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

public class FlaskPasswordEncoder implements PasswordEncoder {

    // Flask default: pbkdf2:sha256:260000$salt$hash
    private static final Pattern FLASK_HASH_PATTERN = Pattern.compile("^pbkdf2:sha256:(\\d+)\\$(.+)\\$(.+)$");

    @Override
    public String encode(CharSequence rawPassword) {
        return rawPassword.toString();
    }

    @Override
    public boolean matches(CharSequence rawPassword, String encodedPassword) {
        if (encodedPassword == null) return false;

        Matcher matcher = FLASK_HASH_PATTERN.matcher(encodedPassword);
        if (matcher.matches()) {
            int iterations = Integer.parseInt(matcher.group(1));
            String salt = matcher.group(2);
            String hash = matcher.group(3);

            try {
                SecretKeyFactory skf = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
                PBEKeySpec spec = new PBEKeySpec(
                    rawPassword.toString().toCharArray(),
                    salt.getBytes(java.nio.charset.StandardCharsets.UTF_8),
                    iterations,
                    256
                );
                byte[] key = skf.generateSecret(spec).getEncoded();

                StringBuilder sb = new StringBuilder();
                for (byte b : key) {
                    sb.append(String.format("%02x", b));
                }
                return sb.toString().equals(hash);

            } catch (Exception e) {
                e.printStackTrace();
                return false;
            }
        }
        return false;
    }
}
