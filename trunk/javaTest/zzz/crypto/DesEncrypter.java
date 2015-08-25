package zzz.crypto;

import java.util.Arrays;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

import org.junit.Test;

public class DesEncrypter {
	Cipher ecipher;
	Cipher dcipher;
	String en = "DES";

	public DesEncrypter() {

	}

	DesEncrypter(SecretKey key) {
		try {
			ecipher = Cipher.getInstance(en);
			dcipher = Cipher.getInstance(en);
			ecipher.init(Cipher.ENCRYPT_MODE, key);
			dcipher.init(Cipher.DECRYPT_MODE, key);

		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	public String encrypt(String str) {
		try {
			// Encode the string into bytes using utf-8
			byte[] utf8 = str.getBytes("UTF8");

			// Encrypt
			byte[] enc = ecipher.doFinal(utf8);

			// Encode bytes to base64 to get a string
			return new sun.misc.BASE64Encoder().encode(enc);
		} catch (Exception e) {
			e.printStackTrace();
		}
		return null;
	}

	public String decrypt(String str) {
		try {
			// Decode base64 to get bytes
			byte[] dec = new sun.misc.BASE64Decoder().decodeBuffer(str);

			// Decrypt
			byte[] utf8 = dcipher.doFinal(dec);

			// Decode using utf-8
			return new String(utf8, "UTF8");
		} catch (Exception e) {
			e.printStackTrace();
		}
		return null;
	}

	@Test
	public void test01() {
		try {
			// Generate a temporary key. In practice, you would save this key.
			// See also Encrypting with DES Using a Pass Phrase.
			KeyGenerator kg = KeyGenerator.getInstance(en);
			// kg.init(56);
			SecretKey key = kg.generateKey();
			System.out.println(Arrays.toString(key.getEncoded()));
			// Create encrypter/decrypter class
			DesEncrypter encrypter = new DesEncrypter(key);

			// Encrypt
			String encrypted = encrypter.encrypt("Don't tell anybody!");
			System.out.println(encrypted);
			// Decrypt
			String decrypted = encrypter.decrypt(encrypted);
			System.out.println(decrypted);
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

}
