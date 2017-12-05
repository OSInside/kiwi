<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv61to62">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv61to62"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.1</literal> to <literal>6.2</literal>.
</para>
<xsl:template match="image" mode="conv61to62">
    <xsl:choose>
        <!-- nothing to do if already at 6.2 -->
        <xsl:when test="@schemaversion > 6.1">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.2">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv61to62"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- add default bootloader if not specified -->
<xsl:template match="type[not(@bootloader)]" mode="conv61to62">
    <xsl:choose>
        <xsl:when test="@image='oem' or @image='vmx'">
            <type bootloader="grub2">
                <xsl:copy-of select="@*[local-name() != 'bootloader']"/>
                <xsl:apply-templates mode="conv61to62"/>
            </type>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy-of select="."/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
