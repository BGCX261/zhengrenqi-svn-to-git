package zzz.core;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.RandomAccessFile;
import java.io.UnsupportedEncodingException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.GregorianCalendar;
import java.util.List;

import org.junit.Test;

import sun.misc.BASE64Encoder;

public class SMSEdit {
	int max = 0;
	String charsetName = "UTF-16";

	public void baseEn() throws Exception {
		String name = "C:\\Temp\\s\\201003.txt";
		File file = new File(name);
		String s = readFile(file, "utf-8");
		System.out.println(s);
		System.out.println(s.length());
		BASE64Encoder encoder = new BASE64Encoder();
		String ens = encoder.encode(s.getBytes("utf-8"));
		String dist = "C:\\Temp\\s\\201003_en.txt";
		writeFile(dist, ens);
	}

	public void baseDe() throws Exception {
		String name = "C:\\Temp\\s\\201003_en.txt";
		File file = new File(name);
		String s = readFile(file, "utf-8");
		System.out.println(s);
		System.out.println(s.length());
		BASE64Encoder encoder = new BASE64Encoder();
		String ens = encoder.encode(s.getBytes("utf-8"));
		String dist = "C:\\Temp\\s\\201003_en.txt";
		writeFile(dist, ens);
	}

	public void mergeFile() throws Exception {
		String folderName = "C:\\Temp\\s\\201003";
		File folder = new File(folderName);
		File[] files = folder.listFiles();
		StringBuilder sb = new StringBuilder();
		for (File file : files) {
			if (file.isFile() && file.getAbsolutePath().endsWith(".txt")) {
				String s = readFile(file, "utf-8");
				sb.append(s).append("\n");
			}
		}
		System.out.println(sb);
		String dist = folder.getParent() + File.separator + "201003.txt";
		System.out.println(dist);
		// writeFile(dist, sb.toString());
		System.out.println(sb.length());
	}

	@Test
	public void parseFiles() throws Exception {
		String recFolderName = "C:\\temp\\收取0911";
		String sendFolderName = "C:\\temp\\发送0911";
		File recFolder = new File(recFolderName);
		File[] recFiles = recFolder.listFiles();
		File sendFolder = new File(sendFolderName);
		File[] sendFiles = sendFolder.listFiles();
		int curRec = 0;
		int curSend = 0;
		StringBuilder sb = new StringBuilder();
		while (curRec < recFiles.length && curSend < sendFiles.length) {
			File recFile = recFiles[curRec];
			File sendFile = sendFiles[curSend];

			if (recFile.getName().compareTo(sendFile.getName()) < 0) {
				sb.append(parseFile(recFile, false)).append("\n");
				curRec++;
			} else {
				sb.append(parseFile(sendFile, true)).append("\n");
				curSend++;
			}
		}
		while (curRec < recFiles.length) {
			File recFile = recFiles[curRec++];
			sb.append(parseFile(recFile, false)).append("\n");
		}
		while (curSend < sendFiles.length) {
			File sendFile = sendFiles[curSend++];
			sb.append(parseFile(sendFile, true)).append("\n");
		}
		System.out.println(sb);
	}

	public String parseFile(File file, boolean isSend) throws Exception {
		StringBuilder sb = new StringBuilder();
		BufferedReader br = null;
		try {
			br = new BufferedReader(new InputStreamReader(new FileInputStream(
					file), charsetName));
			String fileName = file.getName();
			String[] datetime = fileName.split("\\.")[0].split("-");
			SimpleDateFormat sdf1 = new SimpleDateFormat("yyyyMMdd");
			SimpleDateFormat sdf2 = new SimpleDateFormat("yyyy-MM-dd");
			SimpleDateFormat sdf3 = new SimpleDateFormat("HHmmss");
			SimpleDateFormat sdf4 = new SimpleDateFormat("HH:mm:ss");
			String date = sdf2.format(sdf1.parse(datetime[0]));
			String time = sdf4.format(sdf3.parse(datetime[1]));
			String separator = "\t";
			sb.append(date).append(separator).append(time).append(separator)
					.append(isSend ? '发' : '收');
			boolean isContentStart = false;
			while (true) {
				String s = br.readLine();
				if (s == null) {
					break;
				}
				int index0 = s.indexOf("发件人:");
				if (index0 >= 0) {
					int leftIndex = s.indexOf("<", index0 + 4);
					String phoneNumber;
					String name;
					if (leftIndex >= 0) {
						int rightIndex = s.indexOf(">", leftIndex);
						phoneNumber = s.substring(leftIndex + 1, rightIndex);
						name = s.substring(index0 + 4, leftIndex).trim();
					} else {
						name = s.substring(index0 + 4, s.length()).trim();
						phoneNumber = name;
					}
					sb.append(separator).append(name).append(separator).append(
							phoneNumber);
				}
				if (isContentStart) {
					sb.append(s).append(' ');
				}
				if (s.indexOf("内容:") >= 0) {
					isContentStart = true;
					sb.append(separator);
				}

			}
		} finally {
			try {
				br.close();
			} catch (Exception e) {
			}
		}

		return sb.toString().trim();
	}
	@Test
	public void testParseFile() throws Exception {
		String fileName = "C:\\temp\\收取0911\\20091122-022315.txt";
		File file = new File(fileName);
		System.out.println(parseFile(file, false));
	}

	public void test01() {
		int a = "20091121-193215.txt"
				.compareToIgnoreCase("20091122-022315.txt");
		System.out.println(a);
	}

	private String readFile(File file, String charsetName) throws Exception {
		BufferedReader br = null;
		char[] c;
		try {
			br = new BufferedReader(new InputStreamReader(new FileInputStream(
					file), charsetName));
			c = new char[25000];
			int i = br.read(c);
			if (i == 1000) {
				System.out.println(i);
			}
		} finally {
			try {
				br.close();
			} catch (Exception e) {
			}
		}
		return new String(c).trim();
	}

	private void writeFile(String fileName, String s) throws Exception {
		BufferedWriter bw = null;
		try {
			bw = new BufferedWriter(new OutputStreamWriter(
					new FileOutputStream(fileName), "UTF-8"));
			bw.write(s);
			bw.flush();
		} finally {
			try {
				bw.close();
			} catch (Exception e) {
			}
		}
	}

	public void editSend() throws Exception {
		String folderName = "C:\\Temp\\s\\201003receive";
		File folder = new File(folderName);
		File[] files = folder.listFiles();
		for (File file : files) {
			if (file.isFile() && file.getAbsolutePath().endsWith(".txt")) {
				editSendFile(file);
			}
		}
		System.out.println(max);
	}

	public void testEditSendFile() throws Exception {
		String fileName = "20100301-210012.txt";
		File file = new File(fileName);
		editSendFile(file);
	}

	public void editSendFile(File sendFile) throws Exception {
		BufferedReader br = null;

		char[] c;
		try {
			br = new BufferedReader(new InputStreamReader(new FileInputStream(
					sendFile), "UTF-16"));
			c = new char[1500];
			int i = br.read(c);
			if (i == 1000) {
				System.out.println(i);
			}
		} finally {
			try {
				br.close();
			} catch (Exception e) {
			}
		}
		String s = new String(c).trim();
		max = s.length() > max ? s.length() : max;
		// System.out.println(s.length());
		// if (!s.startsWith("发件人")) {
		// return;
		// }

		// s = s.replaceFirst("发件人", "收件人");
		// System.out.println(s);
		String fileName = sendFile.getAbsolutePath();
		/*
		 * File reFile = new File(sendFile.getParent() + File.separator + "bak"
		 * + File.separator + sendFile.getName());
		 * 
		 * // System.out.println(reFile.getAbsolutePath());
		 * sendFile.renameTo(reFile);
		 */
		BufferedWriter bw = null;
		try {
			bw = new BufferedWriter(new OutputStreamWriter(
					new FileOutputStream(fileName), "UTF-8"));
			bw.write(s);
			bw.flush();
		} finally {
			try {
				bw.close();
			} catch (Exception e) {
			}
		}
	}

	public final String readLine(RandomAccessFile in) throws IOException {
		StringBuffer input = new StringBuffer();
		List<Integer> list = new ArrayList<Integer>();
		int c = -1;
		boolean eol = false;
		long start = in.getFilePointer();
		while (!eol) {
			switch (c = in.read()) {
			case -1:
			case '\n':
				eol = true;
				break;
			case '\r':
				eol = true;
				long cur = in.getFilePointer();
				if ((in.read()) != '\n') {
					in.seek(cur);
				}
				break;
			default:
				list.add(c);
				break;
			}
		}

		if ((c == -1) && (input.length() == 0)) {
			return null;
		}
		byte[] cs = new byte[list.size()];
		for (int i = 0; i < cs.length; i++) {
			cs[i] = list.get(i).byteValue();
		}
		System.out.println(cs.length);
		String s = new String(cs, "UTF-16");
		s = s.replace("发件人", "收件人");
		byte[] cs2 = s.getBytes("UTF-16");
		System.out.println(cs.length);
		System.out.println(start);
		in.seek(start);
		System.out.println(in.getFilePointer());
		in.write(cs2);
		return s;
	}
}
