<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv54to55">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv54to55"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.4</literal> to <literal>5.5</literal>.
</para>
<xsl:template match="image" mode="conv54to55">
    <xsl:choose>
        <!-- nothing to do if already at 5.5 -->
        <xsl:when test="@schemaversion > 5.4">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.5">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv54to55"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv54to55">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv54to55"/>
    </xsl:copy>
</xsl:template>

<!-- transform boot-theme to bootloader-theme and bootsplash-theme -->
<xsl:template match="preferences/boot-theme" mode="conv54to55">
    <bootsplash-theme><xsl:value-of select="text()"/></bootsplash-theme>
    <bootloader-theme><xsl:value-of select="text()"/></bootloader-theme>
</xsl:template>

</xsl:stylesheet>
